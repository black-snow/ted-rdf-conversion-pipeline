from airflow.utils.trigger_rule import TriggerRule
from pymongo import MongoClient

from dags.dags_utils import pull_dag_upstream, push_dag_downstream
from ted_sws import config
from ted_sws.core.model.notice import NoticeStatus
from ted_sws.data_manager.adapters.notice_repository import NoticeRepository
from ted_sws.metadata_normaliser.services.metadata_normalizer import normalise_notice_by_id

from airflow.decorators import dag
from airflow.operators.python import get_current_context, BranchPythonOperator, PythonOperator

from dags import DEFAULT_DAG_ARGUMENTS

NOTICE_ID = "notice_id"
MAPPING_SUITE_ID = "mapping_suite_id"


@dag(default_args=DEFAULT_DAG_ARGUMENTS, tags=['worker', 'pipeline'])
def worker_single_notice_process_orchestrator():
    """

    :return:
    """

    def _normalise_notice_metadata():
        """

        :return:
        """
        notice_id = pull_dag_upstream(NOTICE_ID)
        mongodb_client = MongoClient(config.MONGO_DB_AUTH_URL)
        notice_repository = NoticeRepository(mongodb_client=mongodb_client)
        normalised_notice = normalise_notice_by_id(notice_id=notice_id, notice_repository=notice_repository)
        notice_repository.update(notice=normalised_notice)
        push_dag_downstream(NOTICE_ID, notice_id)

    def _check_eligibility_for_transformation():
        notice_id = pull_dag_upstream(NOTICE_ID)
        notice_id = notice_id + "_checked"
        push_dag_downstream(NOTICE_ID, notice_id)
        push_dag_downstream(MAPPING_SUITE_ID, "mapping_suite_id")

    def _preprocess_xml_manifestation():
        notice_id = pull_dag_upstream(NOTICE_ID)
        mapping_suite_id = pull_dag_upstream(MAPPING_SUITE_ID)
        notice_id = notice_id + "_preprocessed"
        push_dag_downstream(NOTICE_ID, notice_id)
        pull_dag_upstream(MAPPING_SUITE_ID, mapping_suite_id)

    def _transform_notice():
        notice_id = pull_dag_upstream(NOTICE_ID)
        mapping_suite_id = pull_dag_upstream(MAPPING_SUITE_ID)
        notice_id = notice_id + "_transformed"
        push_dag_downstream(NOTICE_ID, notice_id)

    def _resolve_entities_in_the_rdf_manifestation():
        notice_id = pull_dag_upstream(NOTICE_ID)
        push_dag_downstream(NOTICE_ID, notice_id)

    def _validate_transformed_rdf_manifestation():
        notice_id = pull_dag_upstream(NOTICE_ID)
        push_dag_downstream(NOTICE_ID, notice_id)

    def _check_eligibility_for_packing_by_validation_report():
        notice_id = pull_dag_upstream(NOTICE_ID)
        push_dag_downstream(NOTICE_ID, notice_id)

    def _generate_mets_package():
        notice_id = pull_dag_upstream(NOTICE_ID)
        push_dag_downstream(NOTICE_ID, notice_id)

    def _check_package_integrity_by_package_structure():
        notice_id = pull_dag_upstream(NOTICE_ID)
        push_dag_downstream(NOTICE_ID, notice_id)

    def _publish_notice_in_cellar():
        notice_id = pull_dag_upstream(NOTICE_ID)
        push_dag_downstream(NOTICE_ID, notice_id)

    def _check_notice_public_availability_in_cellar():
        notice_id = pull_dag_upstream(NOTICE_ID)
        push_dag_downstream(NOTICE_ID, notice_id)

    def _notice_successfully_processed():
        notice_id = pull_dag_upstream(NOTICE_ID)

    def _fail_on_state():
        notice_id = pull_dag_upstream(NOTICE_ID)

    def _check_notice_state_before_transform():
        notice_id = pull_dag_upstream(NOTICE_ID)
        push_dag_downstream(NOTICE_ID, notice_id)
        status = NoticeStatus.ELIGIBLE_FOR_TRANSFORMATION
        if status == NoticeStatus.ELIGIBLE_FOR_TRANSFORMATION:
            return "transform_notice"
        else:
            return "fail_on_state"

    def _check_notice_state_before_generate_mets_package():
        notice_id = pull_dag_upstream(NOTICE_ID)
        push_dag_downstream(NOTICE_ID, notice_id)
        status = NoticeStatus.ELIGIBLE_FOR_PACKAGING
        if status == NoticeStatus.ELIGIBLE_FOR_PACKAGING:
            return "generate_mets_package"
        else:
            return "fail_on_state"

    def _check_notice_state_before_publish_notice_in_cellar():
        notice_id = pull_dag_upstream(NOTICE_ID)
        push_dag_downstream(NOTICE_ID, notice_id)
        status = NoticeStatus.ELIGIBLE_FOR_PUBLISHING
        if status == NoticeStatus.ELIGIBLE_FOR_PUBLISHING:
            return "publish_notice_in_cellar"
        else:
            return "fail_on_state"

    def _check_notice_state_before_notice_successfully_processed():
        notice_id = pull_dag_upstream(NOTICE_ID)
        push_dag_downstream(NOTICE_ID, notice_id)
        status = NoticeStatus.PUBLISHED
        if status == NoticeStatus.PUBLISHED:
            return "notice_successfully_processed"
        else:
            return "fail_on_state"

    normalise_notice_metadata = PythonOperator(
        task_id="normalise_notice_metadata",
        python_callable=_normalise_notice_metadata,
        trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS
    )
    check_eligibility_for_transformation = PythonOperator(
        task_id="check_eligibility_for_transformation",
        python_callable=_check_eligibility_for_transformation,
        trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS
    )

    preprocess_xml_manifestation = PythonOperator(
        task_id="preprocess_xml_manifestation",
        python_callable=_preprocess_xml_manifestation,
        trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS
    )

    transform_notice = PythonOperator(
        task_id="transform_notice",
        python_callable=_transform_notice,
        trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS
    )

    resolve_entities_in_the_rdf_manifestation = PythonOperator(
        task_id="resolve_entities_in_the_rdf_manifestation",
        python_callable=_resolve_entities_in_the_rdf_manifestation,
        trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS
    )

    validate_transformed_rdf_manifestation = PythonOperator(
        task_id="validate_transformed_rdf_manifestation",
        python_callable=_validate_transformed_rdf_manifestation,
        trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS
    )

    check_eligibility_for_packing_by_validation_report = PythonOperator(
        task_id="check_eligibility_for_packing_by_validation_report",
        python_callable=_check_eligibility_for_packing_by_validation_report,
        trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS
    )

    generate_mets_package = PythonOperator(
        task_id="generate_mets_package",
        python_callable=_generate_mets_package,
        trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS
    )

    check_package_integrity_by_package_structure = PythonOperator(
        task_id="check_package_integrity_by_package_structure",
        python_callable=_check_package_integrity_by_package_structure,
        trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS
    )

    publish_notice_in_cellar = PythonOperator(
        task_id="publish_notice_in_cellar",
        python_callable=_publish_notice_in_cellar,
        trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS
    )

    check_notice_public_availability_in_cellar = PythonOperator(
        task_id="check_notice_public_availability_in_cellar",
        python_callable=_check_notice_public_availability_in_cellar,
        trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS
    )

    notice_successfully_processed = PythonOperator(
        task_id="notice_successfully_processed",
        python_callable=_notice_successfully_processed,
        trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS
    )

    fail_on_state = PythonOperator(
        task_id="fail_on_state",
        python_callable=_fail_on_state,
        trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS
    )

    check_notice_state_before_transform = BranchPythonOperator(
        task_id='check_notice_state_before_transform',
        python_callable=_check_notice_state_before_transform,
    )

    check_notice_state_before_generate_mets_package = BranchPythonOperator(
        task_id='check_notice_state_before_generate_mets_package',
        python_callable=_check_notice_state_before_generate_mets_package,
    )

    check_notice_state_before_publish_notice_in_cellar = BranchPythonOperator(
        task_id='check_notice_state_before_publish_notice_in_cellar',
        python_callable=_check_notice_state_before_publish_notice_in_cellar,
    )

    check_notice_state_before_notice_successfully_processed = BranchPythonOperator(
        task_id='check_notice_state_before_notice_successfully_processed',
        python_callable=_check_notice_state_before_notice_successfully_processed,
    )

    normalise_notice_metadata >> check_eligibility_for_transformation >> check_notice_state_before_transform >> [
        preprocess_xml_manifestation, fail_on_state]
    preprocess_xml_manifestation >> transform_notice >> resolve_entities_in_the_rdf_manifestation >> validate_transformed_rdf_manifestation >> check_eligibility_for_packing_by_validation_report
    check_eligibility_for_packing_by_validation_report >> check_notice_state_before_generate_mets_package >> [
        generate_mets_package, fail_on_state]
    generate_mets_package >> check_package_integrity_by_package_structure >> check_notice_state_before_publish_notice_in_cellar >> [
        publish_notice_in_cellar, fail_on_state]
    publish_notice_in_cellar >> check_notice_public_availability_in_cellar >> check_notice_state_before_notice_successfully_processed >> [
        notice_successfully_processed, fail_on_state]

    state_skip_table = {
        NoticeStatus.RAW: "normalise_notice_metadata",
        NoticeStatus.ELIGIBLE_FOR_TRANSFORMATION: "check_eligibility_for_transformation",
        NoticeStatus.ELIGIBLE_FOR_PACKAGING: "generate_mets_package",
        NoticeStatus.ELIGIBLE_FOR_PUBLISHING: "publish_notice_in_cellar",
    }

    def _get_task_run():
        context = get_current_context()
        dag_params = context["dag_run"].conf
        push_dag_downstream(key=NOTICE_ID, value=dag_params["notice_id"])
        return state_skip_table[NoticeStatus[dag_params["notice_status"].split(".")[-1]]]

    branch_task = BranchPythonOperator(
        task_id='start_processing_notice',
        python_callable=_get_task_run,
    )

    branch_task >> [normalise_notice_metadata, check_eligibility_for_transformation, generate_mets_package,
                    publish_notice_in_cellar]


dag = worker_single_notice_process_orchestrator()