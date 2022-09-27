from airflow.decorators import dag, task

from dags import DEFAULT_DAG_ARGUMENTS
from dags.dags_utils import push_dag_downstream
from dags.operators.DagBatchPipelineOperator import NOTICE_IDS_KEY, TriggerNoticeBatchPipelineOperator
from dags.pipelines.notice_selectors_pipelines import notice_ids_selector_by_status
from ted_sws.core.model.notice import NoticeStatus
from ted_sws.event_manager.adapters.event_log_decorator import event_log
from ted_sws.event_manager.model.event_message import TechnicalEventMessage, EventMessageMetadata, \
    EventMessageProcessType

DAG_NAME = "selector_re_publish_process_orchestrator"

RE_PUBLISH_TARGET_NOTICE_STATES = [NoticeStatus.PUBLICLY_UNAVAILABLE, NoticeStatus.ELIGIBLE_FOR_PUBLISHING]
TRIGGER_NOTICE_PROCESS_WORKFLOW_TASK_ID = "trigger_notice_process_workflow"


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
        notice_ids = notice_ids_selector_by_status(notice_statuses=RE_PUBLISH_TARGET_NOTICE_STATES)
        push_dag_downstream(key=NOTICE_IDS_KEY, value=notice_ids)

    trigger_notice_process_workflow = TriggerNoticeBatchPipelineOperator(
        task_id=TRIGGER_NOTICE_PROCESS_WORKFLOW_TASK_ID)
    select_notices_for_re_publish() >> trigger_notice_process_workflow


etl_dag = selector_re_publish_process_orchestrator()
