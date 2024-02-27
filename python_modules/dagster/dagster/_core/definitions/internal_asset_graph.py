from typing import AbstractSet, Iterable, Mapping, Optional, Sequence, Union

from dagster._core.definitions.asset_check_spec import AssetCheckKey
from dagster._core.definitions.asset_checks import AssetChecksDefinition
from dagster._core.definitions.asset_graph import AssetGraph, AssetKeyOrCheckKey, AssetNode
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.backfill_policy import BackfillPolicy
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.freshness_policy import FreshnessPolicy
from dagster._core.definitions.partition import PartitionsDefinition
from dagster._core.definitions.partition_mapping import PartitionMapping
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.selector.subset_selector import DependencyGraph, generate_asset_dep_graph
from dagster._utils.cached_method import cached_method


class LocalAssetNode(AssetNode):
    def __init__(self, key: AssetKey, assets_def: AssetsDefinition):
        self.key = key
        self.assets_def = assets_def

    @property
    @cached_method
    def group_name(self) -> Optional[str]:
        return self.assets_def.group_names_by_key.get(self.key)

    @property
    def is_materializable(self) -> bool:
        return self.assets_def.is_materializable

    @property
    def is_observable(self) -> bool:
        return self.assets_def.is_observable

    @property
    def is_external(self) -> bool:
        return self.assets_def.is_external

    @property
    def is_executable(self) -> bool:
        return self.assets_def.is_executable

    @property
    def is_partitioned(self) -> bool:
        return self.assets_def.partitions_def is not None

    @property
    def partitions_def(self) -> Optional[PartitionsDefinition]:
        return self.assets_def.partitions_def

    @property
    def partition_mappings(self) -> Mapping[AssetKey, PartitionMapping]:
        return self.assets_def.partition_mappings

    @property
    def freshness_policy(self) -> Optional[FreshnessPolicy]:
        return self.assets_def.freshness_policies_by_key.get(self.key)

    @property
    def auto_materialize_policy(self) -> Optional[AutoMaterializePolicy]:
        return self.assets_def.auto_materialize_policies_by_key.get(self.key)

    @property
    def auto_observe_interval_minutes(self) -> Optional[float]:
        return self.assets_def.auto_observe_interval_minutes

    @property
    def backfill_policy(self) -> Optional[BackfillPolicy]:
        return self.assets_def.backfill_policy

    @property
    def code_version(self) -> Optional[str]:
        return self.assets_def.code_versions_by_key.get(self.key)

    @property
    def check_keys(self) -> AbstractSet[AssetCheckKey]:
        return self.assets_def.check_keys


class InternalAssetGraph(AssetGraph[LocalAssetNode]):
    def __init__(
        self,
        asset_nodes: Sequence[LocalAssetNode],
        asset_checks_defs: Sequence[AssetChecksDefinition],
    ):
        self._asset_nodes = asset_nodes
        self._asset_nodes_by_key = {asset.key: asset for asset in asset_nodes}
        self._asset_nodes_by_check_key = {
            **{check_key: asset for asset in asset_nodes for check_key in asset.check_keys},
            **{
                check_key: self._asset_nodes_by_key[check.asset_key]
                for check in asset_checks_defs
                for check_key in check.keys
                if check.asset_key in self._asset_nodes_by_key
            },
        }

        self._asset_checks_defs = asset_checks_defs
        self._asset_checks_defs_by_key = {
            key: check for check in asset_checks_defs for key in check.keys
        }

    @staticmethod
    def from_assets(
        all_assets: Iterable[Union[AssetsDefinition, SourceAsset]],
        asset_checks: Optional[Sequence[AssetChecksDefinition]] = None,
    ) -> "InternalAssetGraph":
        from dagster._core.definitions.external_asset import create_external_asset_from_source_asset

        assets_defs = [
            create_external_asset_from_source_asset(a) if isinstance(a, SourceAsset) else a
            for a in all_assets
        ]
        asset_nodes = [LocalAssetNode(key=k, assets_def=ad) for ad in assets_defs for k in ad.keys]
        return InternalAssetGraph(
            asset_nodes=asset_nodes,
            asset_checks_defs=asset_checks or [],
        )

    @property
    def asset_check_keys(self) -> AbstractSet[AssetCheckKey]:
        return {
            *(key for check in self._asset_checks_defs for key in check.keys),
            *(key for asset in self.assets_defs for key in asset.check_keys),
        }

    @property
    @cached_method
    def assets_defs(self) -> Sequence[AssetsDefinition]:
        return list(dict.fromkeys(asset.assets_def for asset in self._asset_nodes))

    @cached_method
    def get_asset_node_for_check(self, *, key: AssetCheckKey) -> Optional[LocalAssetNode]:
        return self._asset_nodes_by_check_key.get(key)

    @property
    def asset_checks_defs(self) -> Sequence[AssetChecksDefinition]:
        return self._asset_checks_defs

    def get_asset_checks_def(self, asset_check_key: AssetCheckKey) -> AssetChecksDefinition:
        return self._asset_checks_defs_by_key[asset_check_key]

    def has_asset_check(self, asset_check_key: AssetCheckKey) -> bool:
        return asset_check_key in self._asset_checks_defs_by_key

    def includes_materializable_and_external_assets(
        self, asset_keys: AbstractSet[AssetKey]
    ) -> bool:
        """Returns true if the given asset keys contains at least one materializable asset and
        at least one external asset.
        """
        selected_external_assets = self.external_asset_keys & asset_keys
        selected_materializable_assets = self.materializable_asset_keys & asset_keys
        return len(selected_external_assets) > 0 and len(selected_materializable_assets) > 0

    @property
    @cached_method
    def asset_dep_graph(self) -> DependencyGraph[AssetKey]:
        return generate_asset_dep_graph(self.assets_defs, [])

    def get_required_multi_asset_keys(self, asset_key: AssetKey) -> AbstractSet[AssetKey]:
        assets_def = self.get_asset(asset_key).assets_def
        return set() if len(assets_def.keys) <= 1 or assets_def.can_subset else assets_def.keys

    def get_required_asset_and_check_keys(
        self, asset_or_check_key: AssetKeyOrCheckKey
    ) -> AbstractSet[AssetKeyOrCheckKey]:
        if isinstance(asset_or_check_key, AssetKey):
            assets_def = self.get_asset(asset_or_check_key).assets_def
        else:  # AssetCheckKey
            # only checks emitted by AssetsDefinition have required keys
            if self.has_asset_check(asset_or_check_key):
                return set()
            else:
                asset_node = self.get_asset_node_for_check(key=asset_or_check_key)
                if asset_node is None or asset_or_check_key not in asset_node.check_keys:
                    return set()
                assets_def = asset_node.assets_def
        has_checks = len(assets_def.check_keys) > 0
        if assets_def.can_subset or len(assets_def.keys) <= 1 and not has_checks:
            return set()
        else:
            return {*assets_def.keys, *assets_def.check_keys}
