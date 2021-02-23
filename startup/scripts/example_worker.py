import argparse
from functools import partial
import pprint

import msgpack
import msgpack_numpy as mpn

import bluesky_kafka
import databroker.assets.handlers
import event_model
import ophyd.sim

# mpn.patch() is recommended by msgpack-numpy
# as the way to patch msgpack for numpy
mpn.patch()


class ExampleWorker(event_model.SingleRunDocumentRouter):

    def start(self, start_doc):
        print(f"start: {start_doc}")

    def descriptor(self, descriptor_doc):
        print(f"descriptor: {descriptor_doc}")

    def event(self, event_doc):
        print(f"event: {event_doc}")

    def event_page(self, event_page_doc):
        print(f"event_page: {event_page_doc}")

    def stop(self, stop_doc):
        print(f"stop: {stop_doc}")


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "--kafka-bootstrap-servers",
        required=False,
        default="cmb01:9092,cmb02:9092,cmb03:9092",
        help="comma-separated list of Kafka broker host:port",
    )
    arg_parser.add_argument(
        "--kafka-topics",
        required=False,
        default="iss.bluesky.documents",
        type=lambda comma_sep_list: comma_sep_list.split(","),
        help="comma-separated list of Kafka topics from which bluesky documents will be consumed",
    )
    arg_parser.add_argument(
        "--export-dir", required=False, help="output directory for files"
    )

    args = arg_parser.parse_args()
    pprint.pprint(args)
    start_worker(**vars(args))


def start_worker(export_dir, kafka_bootstrap_servers, kafka_topics):
    def worker_factory(name, start_doc, export_dir):
        example_worker = ExampleWorker()
        return [example_worker], []

    dispatcher = bluesky_kafka.RemoteDispatcher(
        topics=kafka_topics,
        group_id="iss-example-worker",
        bootstrap_servers=kafka_bootstrap_servers,
        #deserializer=msgpack.loads,
    )

    rr = event_model.RunRouter(
        [partial(worker_factory, export_dir="export_dir")],
        handler_registry={
            "AD_TIFF": databroker.assets.handlers.AreaDetectorTiffHandler,
            "NPY_SEQ": ophyd.sim.NumpySeqHandler,
        },
    )
    dispatcher.subscribe(rr)
    dispatcher.start()


if __name__ == "__main__":
    main()