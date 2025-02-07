---
title: "Lesson 7: Preparing for a successful run"
module: 'dbt_dagster'
lesson: '7'
---

# Preparing for a successful run

{% callout %}
>💡 **Heads up! This section is optional.** The goal of this lesson was to teach you how to successfully **deploy** to Dagster Cloud, which you completed in the last section. Preparing for a successful run in Dagster Cloud requires using some external services, which may not translate to the external services so we’ve opted to make this section optional.
{% /callout %}

In previous lessons, you followed along by adding our example code to your local project. You successfully materialized the assets in the project and stored the resulting data in a local DuckDB database.

**This section will be a little different.** To keep things simple, we’ll walk you through the steps required to run the pipeline successfully, but we won’t show you how to perform a run in this lesson. Production deployment can be complicated and require a lot of setup. We won't go through setting up the external resources because we want to focus on running your pipeline in Dagster Cloud. For this lesson, assume we already have our storage set up and ready to go.

---

## Deployment overview

Since you'll be deploying your project in production, you'll need production systems to read and write your assets. In this case, we'll use:

- **Amazon S3** to store the files we were saving to our local file system. The data will be small enough to fit within AWS's free tier. For more information on how to set up an S3 bucket, see [this guide](https://www.gormanalysis.com/blog/connecting-to-aws-s3-with-python/).
- **Motherduck** to replace our local DuckDB instance and query the data in our S3 bucket. Motherduck is a cloud-based data warehouse that can be used to store and query data that is currently free to setup. For more information on how to set up Motherduck, see [their documentation](https://motherduck.com/docs/getting-started), along with how to [connect it to your AWS S3 bucket](https://motherduck.com/docs/integrations/amazon-s3).

The code you cloned in the starter project already has some logic to dynamically switch between local and cloud storage, along with the paths to reference. To trigger the switch, you can set an environment variable called `DAGSTER_ENVIRONMENT` and set it to `prod`. This will tell the pipeline to use the production paths and storage.

In summary, before you can run this pipeline in Dagster Cloud, you’ll need to:

1. Set up an S3 bucket to store the files/assets that we download and generate
2. Sign up for a free Motherduck account to replace our local DuckDB instance
3. Connect an S3 user with access to the S3 bucket to the Motherduck account
4. Add a new production target to the dbt project
5. Add the environment variables for the S3 user and Motherduck token to Dagster Cloud

We’ll show you how to do 4 and 5 so you can do this with your credentials when you’re ready.

---

## Adding a production target to profiles.yml

The first step we’ll take is to add a second target to the `dagster_dbt_university` profile in our project’s `analytics/profiles.yml`. A [‘target’ in dbt](https://docs.getdbt.com/docs/core/connect-data-platform/connection-profiles#understanding-targets-in-profiles) describes a connection to a data warehouse, which up until this point in the course, has a local DuckDB instance.

To maintain the separation of our development and production environments, we’ll add a `prod` target to our project’s profiles:

```yaml
dagster_dbt_university:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: '../{{ env_var("DUCKDB_DATABASE", "data/staging/data.duckdb") }}'
    prod:
      type: duckdb
      path: '{{ env_var("MOTHERDUCK_TOKEN", "") }}'
```

Because we’re still using DuckDB-backed database, our `type` will also be `duckdb` for `prod`. Save and commit the file to git before continuing.

**Note:** While dbt supports more platforms than just DuckDB, our project is set up to only work with this database type. If you use a different platform `type` for future projects, the configuration will vary depending on the platform being connected. Refer to [dbt’s documentation](https://docs.getdbt.com/docs/supported-data-platforms) for more information and examples.

---

## Adding a prod target to deploy.yml

Next, we need to update the dbt commands in the `.github/workflows/deploy.yml` file to target the new `prod` profile. This will ensure that dbt uses the correct connection details when the GitHub Action runs as part of our Dagster Cloud deployment.

Open the file, scroll to the dbt step you added, and add `-- target prod` after the `dbt parse` command. This command should be on or around line 52:

```bash
- name: Parse dbt project and package with Dagster project
  if: steps.prerun.outputs.result == 'pex-deploy'
  run: |
    pip install pip --upgrade
    pip install dbt-duckdb
    cd project-repo/analytics
    dbt deps
    dbt parse --target prod    ## add this flag
  shell: bash
```

Save and commit the file to git. Don’t forget to push to remote!

---

## Adding environment variables to Dagster Cloud

The last step in preparing for a successful run is to move environment variables to Dagster Cloud. These variables were available to us via the `.env` file while we were working locally, but now that we’ve moved to a different environment, we’ll need to make them accessible again.

### Environment variables

The following table contains the environment variables we need to create in Dagster Cloud:

{% table %}

- Variable {% width="30%" %}
- Description

---

- `DUCKDB_DATABASE`
- todo

---

- `DAGSTER_ENVIRONMENT`
- Set this to `prod`

---

- `AWS_ACCESS_KEY_ID`
- The access key ID for the S3 bucket.

---

- `AWS_SECRET_ACCESS_KEY`
- The secret access key associated with the S3 bucket.

---

- `AWS_REGION`
- The region the S3 bucket is located in.

---

- `S3_BUCKET_NAME`
- The name of the S3 bucket, by default `"s3://dagster-university/"`

{% /table %}

### Creating environment variables

1. In the Dagster Cloud UI, click **Deployment > Environment variables**.
2. Click the **Add environment variable** button on the right side of the screen.
3. In the **Create environment variable** window, fill in the following:
    1. **Name** - The name of the environment variable. For example: `DUCKDB_DATABASE`
    2. **Value** - The value of the environment variable.
    3. **Code location scope**  - Deselect the **All code locations** option and check only the code location for this course’s project.
4. Click **Save.**

Repeat these steps until all the environment variables have been added.

---

## Running the pipeline

TODO: Add once unblocked