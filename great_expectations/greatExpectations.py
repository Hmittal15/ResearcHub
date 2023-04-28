import great_expectations as gx
from great_expectations.core.batch import Batch, BatchRequest, RuntimeBatchRequest
from great_expectations.core.yaml_handler import YAMLHandler

def ge():
    yaml = YAMLHandler()
    context = gx.get_context()
    datasource_yaml = rf"""
        name: my_s3_datasource
        class_name: Datasource
        execution_engine:
            class_name: PandasExecutionEngine
        data_connectors:
            default_runtime_data_connector_name:
                class_name: RuntimeDataConnector
                batch_identifiers:
                    - default_identifier_name
            default_inferred_data_connector_name:
                class_name: InferredAssetS3DataConnector
                bucket: greatexpectations
                prefix: data/
                default_regex:
                    pattern: (.*)\.csv
                    group_names:
                        - data_asset_name
        """
    print(datasource_yaml)
    context.test_yaml_config(datasource_yaml)
    context.add_datasource(**yaml.load(datasource_yaml))
    context.list_datasources()
    batch_request = RuntimeBatchRequest(
        datasource_name="my_s3_datasource",
        data_connector_name="default_runtime_data_connector_name",
        data_asset_name="Springer_meta_data",  # this can be anything that identifies this data_asset for you
        runtime_parameters={"path": "s3://greatexpectations/data/SPRINGER_METADATA.csv"},  # Add your S3 path here.
        batch_identifiers={"default_identifier_name": "default_identifier"},
        )
    context.add_or_update_expectation_suite(expectation_suite_name="Springer_meta_data_suite")
    validator = context.get_validator(
        batch_request=batch_request, expectation_suite_name="Springer_meta_data_suite"
    )
    print(validator.head())
    validator.expect_column_values_to_not_be_null(column="CATEGORY")
    validator.expect_column_values_to_not_be_null(column="TYPE")
    validator.expect_column_values_to_not_be_null(column="TITLE")
    validator.expect_column_values_to_not_be_null(column="LANGUAGE")
    validator.expect_column_values_to_not_be_null(column="DATE")
    validator.expect_column_values_to_not_be_null(column="ID")
    validator.expect_column_values_to_not_be_null(column="AUTHORS")
    validator.expect_column_values_to_not_be_null(column="DOC_URL")

    # Check that the "URL" column values match the regular expression pattern for URLs
    url_pattern = r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+"
    validator.expect_column_values_to_match_regex(column="DOC_URL", regex=url_pattern)
    # Check that the "code" column values have a length of 2
    validator.expect_column_value_lengths_to_be_between(column="LANGUAGE", min_value=2, max_value=5)

    validator.expect_column_values_to_match_strftime_format(column="DATE", strftime_format='%Y-%m-%d')

    validator.save_expectation_suite(discard_failed_expectations=False)

    my_checkpoint_name = "first_checkpoint"
    my_checkpoint_config = f"""
    name: {my_checkpoint_name}
    config_version: 1.0
    class_name: SimpleCheckpoint
    run_name_template: "%Y%m%d-%H%M%S-my-run-name-template"
    """

    my_checkpoint = context.test_yaml_config(my_checkpoint_config)

    context.add_or_update_checkpoint(**yaml.load(my_checkpoint_config))

    checkpoint_result = context.run_checkpoint(
        checkpoint_name=my_checkpoint_name,
        validations=[
            {
                "batch_request": batch_request,
                "expectation_suite_name": "Springer_meta_data_suite",
            }
        ],
        )
    
    context.open_data_docs()

if __name__ == "__main__":
    ge()
