import itertools
import warnings
from collections import defaultdict
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    DefaultDict,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
)

import dagster._check as check
from dagster._core.definitions.asset_check_spec import AssetCheckKey
from dagster._core.definitions.asset_spec import AssetExecutionType
from dagster._core.definitions.assets_job import ASSET_BASE_JOB_PREFIX
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.host_representation.external import ExternalRepository
from dagster._core.host_representation.handle import RepositoryHandle
from dagster._core.selector.subset_selector import DependencyGraph
from dagster._core.workspace.workspace import IWorkspace
from dagster._utils.cached_method import cached_method

from .asset_graph import AssetGraph, AssetKeyOrCheckKey, AssetNode
from .backfill_policy import BackfillPolicy
from .events import AssetKey
from .freshness_policy import FreshnessPolicy
from .partition import PartitionsDefinition
from .partition_mapping import PartitionMapping

if TYPE_CHECKING:
    from dagster._core.host_representation.external_data import (
        ExternalAssetCheck,
        ExternalAssetNode,
    )


class GlobalAssetNode(AssetNode):
    def __init__(
        self, key, repo_node_pairs: Sequence[Tuple[RepositoryHandle, "ExternalAssetNode"]]
    ):
        self.key = key
        self._repo_node_pairs = repo_node_pairs
        self._external_asset_nodes = [node for _, node in repo_node_pairs]

    ##### COMMON ASSET NODE INTERFACE

    @property
    @cached_method
    def group_name(self) -> Optional[str]:
        return self._first_node.group_name

    @property
    @cached_method
    def is_materializable(self) -> bool:
        return any(node.is_materializable for node in self._external_asset_nodes)

    @property
    @cached_method
    def is_observable(self) -> bool:
        return any(node.is_observable for node in self._external_asset_nodes)

    @property
    @cached_method
    def is_external(self) -> bool:
        return all(node.is_external for node in self._external_asset_nodes)

    @property
    @cached_method
    def is_executable(self) -> bool:
        return any(node.is_executable for node in self._external_asset_nodes)

    def is_partitioned(self) -> bool:
        return self._first_node.partitions_def_data is not None

    @property
    @cached_method
    def partitions_def(self) -> Optional[PartitionsDefinition]:
        external_def = self._first_node.partitions_def_data
        return external_def.get_partitions_definition() if external_def else None

    @property
    def partition_mappings(self) -> Mapping[AssetKey, PartitionMapping]:
        if self.is_materializable:
            return {
                dep.upstream_asset_key: dep.partition_mapping
                for dep in self._materializable_node.dependencies
                if dep.partition_mapping is not None
            }
        else:
            return {}

    @property
    def freshness_policy(self) -> Optional[FreshnessPolicy]:
        # It is currently not possible to access the freshness policy for an observation definition
        # if a materialization definition also exists. This needs to be fixed.
        return self._first_executable_node.freshness_policy

    @property
    def auto_materialize_policy(self) -> Optional[AutoMaterializePolicy]:
        return self._materializable_node.auto_materialize_policy if self.is_materializable else None

    @property
    def auto_observe_interval_minutes(self) -> Optional[float]:
        return self._observable_node.auto_observe_interval_minutes if self.is_observable else None

    @property
    def backfill_policy(self) -> Optional[BackfillPolicy]:
        return self._materializable_node.backfill_policy if self.is_materializable else None

    @property
    def code_version(self) -> Optional[str]:
        # It is currently not possible to access the code version for an observation definition if a
        # materialization definition also exists. This needs to be fixed.
        return self._first_executable_node.code_version

    ##### GLOBAL-SPECIFIC METHODS

    @property
    def atomic_execution_unit_id(self) -> Optional[str]:
        # It is currently not possible to access the atomic execution unit ID for an observation
        # definition if a materialization definition also exists. This needs to be fixed.
        return self._first_executable_node.atomic_execution_unit_id

    @property
    def job_names(self) -> Sequence[str]:
        # It is currently not possible to access the job names for an observation definition if a
        # materialization definition also exists. This needs to be fixed.
        return self._first_executable_node.job_names if self.is_executable else []

    ##### HELPERS

    @property
    @cached_method
    def _first_node(self) -> "ExternalAssetNode":
        return next(node for node in self._external_asset_nodes)

    @property
    @cached_method
    def _materializable_node(self) -> "ExternalAssetNode":
        return next(node for node in self._external_asset_nodes if node.is_materializable)

    @property
    @cached_method
    def _first_executable_node(self) -> "ExternalAssetNode":
        # Return a materialization node if it exists, otherwise return an observable node if it
        # exists. Error if neither exists. This exists to preserve implicit behavior, where the
        # materialization node was previously preferred over the observable node. This is a
        # temporary measure until we can appropriately scope the accessors that could apply to
        # either a materialization or observation node.
        return next(
            itertools.chain(
                (node for node in self._external_asset_nodes if node.is_materializable),
                (node for node in self._external_asset_nodes if node.is_observable),
            )
        )

    @property
    @cached_method
    def _observable_node(self) -> "ExternalAssetNode":
        return next((node for node in self._external_asset_nodes if node.is_observable))


class ExternalAssetGraph(AssetGraph[GlobalAssetNode]):
    def __init__(
        self,
        asset_nodes: Sequence[GlobalAssetNode],
        asset_checks_by_key: Mapping[AssetCheckKey, "ExternalAssetCheck"],
        repo_handles_by_key: Mapping[AssetKey, RepositoryHandle],
    ):
        self._asset_nodes = asset_nodes
        self._asset_checks_by_key = asset_checks_by_key
        self._repo_handles_by_key = repo_handles_by_key

    @classmethod
    def from_workspace(cls, context: IWorkspace) -> "ExternalAssetGraph":
        code_locations = (
            location_entry.code_location
            for location_entry in context.get_workspace_snapshot().values()
            if location_entry.code_location
        )
        repos = (
            repo
            for code_location in code_locations
            for repo in code_location.get_repositories().values()
        )
        repo_handle_external_asset_nodes: Sequence[
            Tuple[RepositoryHandle, "ExternalAssetNode"]
        ] = []
        asset_checks: Sequence["ExternalAssetCheck"] = []

        for repo in repos:
            for external_asset_node in repo.get_external_asset_nodes():
                repo_handle_external_asset_nodes.append((repo.handle, external_asset_node))

            asset_checks.extend(repo.get_external_asset_checks())

        return cls.from_repository_handles_and_external_asset_nodes(
            repo_handle_external_asset_nodes=repo_handle_external_asset_nodes,
            external_asset_checks=asset_checks,
        )

    @classmethod
    def from_external_repository(
        cls, external_repository: ExternalRepository
    ) -> "ExternalAssetGraph":
        return cls.from_repository_handles_and_external_asset_nodes(
            repo_handle_external_asset_nodes=[
                (external_repository.handle, asset_node)
                for asset_node in external_repository.get_external_asset_nodes()
            ],
            external_asset_checks=external_repository.get_external_asset_checks(),
        )

    @classmethod
    def from_repository_handles_and_external_asset_nodes(
        cls,
        repo_handle_external_asset_nodes: Sequence[Tuple[RepositoryHandle, "ExternalAssetNode"]],
        external_asset_checks: Sequence["ExternalAssetCheck"],
    ) -> "ExternalAssetGraph":
        repo_handles_by_key = {
            node.asset_key: repo_handle
            for repo_handle, node in repo_handle_external_asset_nodes
            if node.is_executable
        }

        # Split the nodes into materializable, observable, and unexecutable nodes. Observable and
        # unexecutable `ExternalAssetNode` represent both source and external assets-- the
        # "External" in "ExternalAssetNode" is unrelated to the "external" in "external asset", this
        # is just an unfortunate naming collision. `ExternalAssetNode` will be renamed eventually.
        materializable_node_pairs: List[Tuple[RepositoryHandle, "ExternalAssetNode"]] = []
        observable_node_pairs: List[Tuple[RepositoryHandle, "ExternalAssetNode"]] = []
        unexecutable_node_pairs: List[Tuple[RepositoryHandle, "ExternalAssetNode"]] = []
        for repo_handle, node in repo_handle_external_asset_nodes:
            if node.is_source and node.is_observable:
                observable_node_pairs.append((repo_handle, node))
            elif node.is_source:
                unexecutable_node_pairs.append((repo_handle, node))
            else:
                materializable_node_pairs.append((repo_handle, node))

        _warn_on_duplicate_nodes(materializable_node_pairs, AssetExecutionType.MATERIALIZATION)
        _warn_on_duplicate_nodes(observable_node_pairs, AssetExecutionType.OBSERVATION)

        # It is possible for multiple nodes to exist that share the same key. This is invalid if
        # more than one node is materializable or if more than one node is observable. It is valid
        # if there is at most one materializable node and at most one observable node, with all
        # other nodes unexecutable. The asset graph will receive only a single `ExternalAssetNode`
        # representing the asset. This will always be the materializable node if one exists; then
        # the observable node if it exists; then finally the first-encountered unexecutable node.
        node_pairs_by_key: Dict[
            AssetKey, List[Tuple[RepositoryHandle, "ExternalAssetNode"]]
        ] = defaultdict(list)
        for repo_handle, node in (
            *materializable_node_pairs,
            *observable_node_pairs,
            *unexecutable_node_pairs,
        ):
            node_pairs_by_key[node.asset_key].append((repo_handle, node))

        asset_nodes = [
            GlobalAssetNode(key=k, repo_node_pairs=[(r, n) for r, n in v])
            for k, v in node_pairs_by_key.items()
        ]

        asset_checks_by_key: Dict[AssetCheckKey, "ExternalAssetCheck"] = {}
        for asset_check in external_asset_checks:
            asset_checks_by_key[asset_check.key] = asset_check

        return cls(
            asset_nodes,
            asset_checks_by_key,
            repo_handles_by_key=repo_handles_by_key,
        )

    @property
    def asset_checks(self) -> Sequence["ExternalAssetCheck"]:
        return list(self._asset_checks_by_key.values())

    def get_asset_check(self, asset_check_key: AssetCheckKey) -> "ExternalAssetCheck":
        return self._asset_checks_by_key[asset_check_key]

    @property
    @cached_method
    def asset_dep_graph(self) -> DependencyGraph[AssetKey]:
        upstream = {node.key: set() for node in self.asset_nodes}
        downstream = {node.key: set() for node in self.asset_nodes}
        for key in self.materializable_asset_keys:
            node = self.get_asset(key)
            for dep in node._materializable_node.dependencies:  # noqa: SLF001t
                upstream[node.key].add(dep.upstream_asset_key)
                downstream[dep.upstream_asset_key].add(node.key)
        return {"upstream": upstream, "downstream": downstream}

    def asset_keys_for_job(self, job_name: str) -> AbstractSet[AssetKey]:
        return {node.key for node in self.asset_nodes if job_name in node.job_names}

    def get_required_asset_and_check_keys(
        self, asset_or_check_key: AssetKeyOrCheckKey
    ) -> AbstractSet[AssetKeyOrCheckKey]:
        if isinstance(asset_or_check_key, AssetKey):
            atomic_execution_unit_id = self.get_asset(asset_or_check_key).atomic_execution_unit_id
        else:  # AssetCheckKey
            atomic_execution_unit_id = self.get_asset_check(
                asset_or_check_key
            ).atomic_execution_unit_id
        if atomic_execution_unit_id is None:
            return set()
        else:
            return {
                *(
                    node.key
                    for node in self.asset_nodes
                    if node.is_executable
                    and node.atomic_execution_unit_id == atomic_execution_unit_id
                ),
                *(
                    node.key
                    for node in self.asset_checks
                    if node.atomic_execution_unit_id == atomic_execution_unit_id
                ),
            }

    def get_required_multi_asset_keys(self, asset_key: AssetKey) -> AbstractSet[AssetKey]:
        return {
            key
            for key in self.get_required_asset_and_check_keys(asset_key)
            if isinstance(key, AssetKey)
        }

    @property
    @cached_method
    def all_job_names(self) -> AbstractSet[str]:
        return {job_name for node in self.asset_nodes for job_name in node.job_names}

    @property
    def repository_handles_by_key(self) -> Mapping[AssetKey, RepositoryHandle]:
        return self._repo_handles_by_key

    def get_repository_handle(self, asset_key: AssetKey) -> RepositoryHandle:
        return self._repo_handles_by_key[asset_key]

    def get_materialization_job_names(self, asset_key: AssetKey) -> Sequence[str]:
        """Returns the names of jobs that materialize this asset."""
        return self.get_asset(asset_key).job_names

    def get_materialization_asset_keys_for_job(self, job_name: str) -> Sequence[AssetKey]:
        """Returns asset keys that are targeted for materialization in the given job."""
        return [
            k
            for k in self.materializable_asset_keys
            if job_name in self.get_materialization_job_names(k)
        ]

    def get_implicit_job_name_for_assets(
        self,
        asset_keys: Iterable[AssetKey],
        external_repo: Optional[ExternalRepository],
    ) -> Optional[str]:
        """Returns the name of the asset base job that contains all the given assets, or None if there is no such
        job.

        Note: all asset_keys should be in the same repository.
        """
        if all(self.get_asset(asset_key).is_observable for asset_key in asset_keys):
            if external_repo is None:
                check.failed(
                    "external_repo must be passed in when getting job names for observable assets"
                )
            # for observable assets, we need to select the job based on the partitions def
            target_partitions_defs = {
                self.get_partitions_def(asset_key) for asset_key in asset_keys
            }
            check.invariant(len(target_partitions_defs) == 1, "Expected exactly one partitions def")
            target_partitions_def = next(iter(target_partitions_defs))

            # create a mapping from job name to the partitions def of that job
            partitions_def_by_job_name = {}
            for (
                external_partition_set_data
            ) in external_repo.external_repository_data.external_partition_set_datas:
                if external_partition_set_data.external_partitions_data is None:
                    partitions_def = None
                else:
                    partitions_def = external_partition_set_data.external_partitions_data.get_partitions_definition()
                partitions_def_by_job_name[external_partition_set_data.job_name] = partitions_def
            # add any jobs that don't have a partitions def
            for external_job in external_repo.get_all_external_jobs():
                job_name = external_job.external_job_data.name
                if job_name not in partitions_def_by_job_name:
                    partitions_def_by_job_name[job_name] = None
            # find the job that matches the expected partitions definition
            for job_name, external_partitions_def in partitions_def_by_job_name.items():
                asset_keys_for_job = self.asset_keys_for_job(job_name)
                if not job_name.startswith(ASSET_BASE_JOB_PREFIX):
                    continue
                if (
                    # unpartitioned observable assets may be materialized in any job
                    target_partitions_def is None
                    or external_partitions_def == target_partitions_def
                ) and all(asset_key in asset_keys_for_job for asset_key in asset_keys):
                    return job_name
        else:
            for job_name in self.all_job_names:
                asset_keys_for_job = self.asset_keys_for_job(job_name)
                if not job_name.startswith(ASSET_BASE_JOB_PREFIX):
                    continue
                if all(asset_key in self.asset_keys_for_job(job_name) for asset_key in asset_keys):
                    return job_name
        return None

    def split_asset_keys_by_repository(
        self, asset_keys: AbstractSet[AssetKey]
    ) -> Sequence[AbstractSet[AssetKey]]:
        asset_keys_by_repo = defaultdict(set)
        for asset_key in asset_keys:
            repo_handle = self.get_repository_handle(asset_key)
            asset_keys_by_repo[(repo_handle.location_name, repo_handle.repository_name)].add(
                asset_key
            )
        return list(asset_keys_by_repo.values())


def _warn_on_duplicate_nodes(
    node_pairs: Sequence[Tuple[RepositoryHandle, "ExternalAssetNode"]],
    execution_type: AssetExecutionType,
) -> None:
    repo_handles_by_asset_key: DefaultDict[AssetKey, List[RepositoryHandle]] = defaultdict(list)
    for repo_handle, node in node_pairs:
        repo_handles_by_asset_key[node.asset_key].append(repo_handle)

    duplicates = {k: v for k, v in repo_handles_by_asset_key.items() if len(v) > 1}
    duplicate_lines = []
    for asset_key, repo_handles in duplicates.items():
        locations = [repo_handle.code_location_origin.location_name for repo_handle in repo_handles]
        duplicate_lines.append(f"  {asset_key.to_string()}: {locations}")
    duplicate_str = "\n".join(duplicate_lines)
    if duplicates:
        warnings.warn(
            f"Found {execution_type.value} nodes for some asset keys in multiple code locations."
            f" Only one {execution_type.value} node is allowed per asset key. Duplicates:\n {duplicate_str}"
        )
