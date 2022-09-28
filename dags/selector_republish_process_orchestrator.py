from airflow.decorators import dag, task

from dags import DEFAULT_DAG_ARGUMENTS
from dags.dags_utils import push_dag_downstream, get_dag_param
from dags.notice_process_workflow import NOTICE_PUBLISH_PIPELINE_TASK_ID
from dags.operators.DagBatchPipelineOperator import NOTICE_IDS_KEY, TriggerNoticeBatchPipelineOperator, \
    EXECUTE_ONLY_ONE_STEP_KEY
from dags.pipelines.notice_selectors_pipelines import notice_ids_selector_by_status
from ted_sws.core.model.notice import NoticeStatus
from ted_sws.event_manager.adapters.event_log_decorator import event_log
from ted_sws.event_manager.model.event_message import TechnicalEventMessage, EventMessageMetadata, \
    EventMessageProcessType

DAG_NAME = "selector_re_publish_process_orchestrator"

RE_PUBLISH_TARGET_NOTICE_STATES = [NoticeStatus.PUBLICLY_UNAVAILABLE, NoticeStatus.ELIGIBLE_FOR_PUBLISHING]
TRIGGER_NOTICE_PROCESS_WORKFLOW_TASK_ID = "trigger_notice_process_workflow"
FORM_NUMBER_DAG_PARAM = "form_number"
START_DATE_DAG_PARAM = "start_date"
END_DATE_DAG_PARAM = "end_date"
XSD_VERSION_DAG_PARAM = "xsd_version"


@dag(default_args=DEFAULT_DAG_ARGUMENTS,
     schedule_interval=None,
     tags=['selector', 're-publish'])
def selector_re_publish_process_orchestrator():
    @task
    @event_log(TechnicalEventMessage(
        message="select_notices_for_re_publish",
        metadata=EventMessageMetadata(
            process_type=EventMessageProcessType.DAG, process_name=DAG_NAME
        ))
    )
    def select_notices_for_re_publish():
        form_number = get_dag_param(key=FORM_NUMBER_DAG_PARAM)
        start_date = get_dag_param(key=START_DATE_DAG_PARAM)
        end_date = get_dag_param(key=END_DATE_DAG_PARAM)
        xsd_version = get_dag_param(key=XSD_VERSION_DAG_PARAM)
        notice_ids = notice_ids_selector_by_status(notice_statuses=RE_PUBLISH_TARGET_NOTICE_STATES,
                                                   form_number=form_number, start_date=start_date,
                                                   end_date=end_date, xsd_version=xsd_version)
        push_dag_downstream(key=NOTICE_IDS_KEY, value=notice_ids)

    trigger_notice_process_workflow = TriggerNoticeBatchPipelineOperator(
        task_id=TRIGGER_NOTICE_PROCESS_WORKFLOW_TASK_ID,
        execute_only_one_step=get_dag_param(key=EXECUTE_ONLY_ONE_STEP_KEY),
        start_with_step_name=NOTICE_PUBLISH_PIPELINE_TASK_ID
    )
    select_notices_for_re_publish() >> trigger_notice_process_workflow


etl_dag = selector_re_publish_process_orchestrator()
