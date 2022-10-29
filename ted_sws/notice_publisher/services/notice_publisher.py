import base64
import pathlib
import tempfile

from ted_sws import config
from ted_sws.core.model.manifestation import RDFManifestation
from ted_sws.core.model.notice import Notice, NoticeStatus
from ted_sws.data_manager.adapters.notice_repository import NoticeRepositoryABC
from ted_sws.notice_packager import DEFAULT_NOTICE_PACKAGE_EXTENSION
from ted_sws.notice_publisher.adapters.s3_notice_publisher import S3Publisher, DEFAULT_S3_RDF_CONTENT_TYPE
from ted_sws.notice_publisher.adapters.sftp_notice_publisher import SFTPPublisher
from ted_sws.notice_publisher.adapters.sftp_publisher_abc import SFTPPublisherABC
from ted_sws.notice_publisher.model.s3_publish_result import S3PublishResult
from ted_sws.notice_transformer.services.notice_transformer import DEFAULT_TRANSFORMATION_FILE_EXTENSION

DEFAULT_NOTICE_S3_BUCKET_NAME = config.S3_PUBLISH_NOTICE_BUCKET or "notice"
DEFAULT_NOTICE_RDF_S3_BUCKET_NAME = config.S3_PUBLISH_NOTICE_RDF_BUCKET or "notice-rdf"


def publish_notice(notice: Notice, publisher: SFTPPublisherABC = None,
                   remote_folder_path: str = None) -> bool:
    """
        This function publishes the METS manifestation for a Notice in Cellar.
    """
    publisher = publisher if publisher else SFTPPublisher()
    remote_folder_path = remote_folder_path if remote_folder_path else config.SFTP_PATH
    mets_manifestation = notice.mets_manifestation
    if not mets_manifestation or not mets_manifestation.object_data:
        raise ValueError("Notice does not have a METS manifestation to be published.")

    package_content = base64.b64decode(bytes(mets_manifestation.object_data, encoding='utf-8'), validate=True)
    remote_notice_path = f"{remote_folder_path}/{notice.ted_id}{DEFAULT_NOTICE_PACKAGE_EXTENSION}"
    source_file = tempfile.NamedTemporaryFile()
    source_file.write(package_content)
    try:
        publisher.connect()
        if publisher.publish(source_path=str(pathlib.Path(source_file.name)),
                             remote_path=remote_notice_path):
            notice.update_status_to(NoticeStatus.PUBLISHED)
        publisher.disconnect()
    except Exception as e:
        raise Exception(f"Notice {notice.ted_id} could not be published: " + str(e))

    return notice.status == NoticeStatus.PUBLISHED


def publish_notice_by_id(notice_id: str, notice_repository: NoticeRepositoryABC,
                         publisher: SFTPPublisherABC = None, remote_folder_path: str = None) -> bool:
    """
        This function publishes the METS manifestation of a Notice, based on notice_id, in Cellar.
    """
    notice = notice_repository.get(reference=notice_id)
    result = publish_notice(notice=notice, publisher=publisher, remote_folder_path=remote_folder_path)
    if result:
        notice_repository.update(notice=notice)
    return result


def publish_notice_into_s3(notice: Notice, s3_publisher: S3Publisher = S3Publisher(),
                           bucket_name: str = DEFAULT_NOTICE_S3_BUCKET_NAME) -> bool:
    """

    """
    mets_manifestation = notice.mets_manifestation
    if not mets_manifestation or not mets_manifestation.object_data:
        raise ValueError("Notice does not have a METS manifestation to be published.")

    package_content = base64.b64decode(bytes(mets_manifestation.object_data, encoding='utf-8'), validate=True)
    result: S3PublishResult = s3_publisher.publish(bucket_name=bucket_name,
                                                   object_name=f"{notice.ted_id}{DEFAULT_NOTICE_PACKAGE_EXTENSION}",
                                                   data=package_content)
    if result:
        notice.update_status_to(NoticeStatus.PUBLISHED)

    return notice.status == NoticeStatus.PUBLISHED


def publish_notice_into_s3_by_id(notice_id: str, notice_repository: NoticeRepositoryABC,
                                 s3_publisher: S3Publisher = S3Publisher(),
                                 bucket_name: str = DEFAULT_NOTICE_S3_BUCKET_NAME) -> bool:
    notice = notice_repository.get(reference=notice_id)
    result = publish_notice_into_s3(notice=notice, bucket_name=bucket_name, s3_publisher=s3_publisher)
    if result:
        notice_repository.update(notice=notice)
    return result


def publish_notice_rdf_into_s3(notice: Notice, s3_publisher: S3Publisher = S3Publisher(),
                               bucket_name: str = DEFAULT_NOTICE_RDF_S3_BUCKET_NAME) -> bool:
    """

    """
    rdf_manifestation: RDFManifestation = notice.rdf_manifestation
    result: bool = publish_notice_rdf_content_into_s3(
        rdf_manifestation=rdf_manifestation,
        object_name=f"{notice.ted_id}{DEFAULT_TRANSFORMATION_FILE_EXTENSION}",
        s3_publisher=s3_publisher,
        bucket_name=bucket_name
    )
    return result


def publish_notice_rdf_into_s3_by_id(notice_id: str, notice_repository: NoticeRepositoryABC,
                                     s3_publisher: S3Publisher = S3Publisher(),
                                     bucket_name: str = DEFAULT_NOTICE_RDF_S3_BUCKET_NAME) -> bool:
    notice = notice_repository.get(reference=notice_id)
    return publish_notice_rdf_into_s3(notice=notice, bucket_name=bucket_name, s3_publisher=s3_publisher)


def publish_notice_rdf_content_into_s3(rdf_manifestation: RDFManifestation,
                                       object_name: str,
                                       s3_publisher: S3Publisher = S3Publisher(),
                                       bucket_name: str = DEFAULT_NOTICE_RDF_S3_BUCKET_NAME) -> bool:
    if not rdf_manifestation or not rdf_manifestation.object_data:
        raise ValueError("Notice does not have a RDF manifestation to be published.")

    rdf_content = base64.b64decode(bytes(rdf_manifestation.object_data, encoding='utf-8'), validate=True)
    result: S3PublishResult = s3_publisher.publish(
        bucket_name=bucket_name,
        object_name=object_name,
        data=rdf_content,
        content_type=DEFAULT_S3_RDF_CONTENT_TYPE
    )

    return bool(result)
