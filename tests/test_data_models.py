import unittest

from src.data.api_reference import (
    AllSP1ForecastAromeRecords,
    AllSP2ForecastAromeRecords,
    BronzeObservationListeStationsRecords,
    SilverForecastAromeRecords,
)
from src.data.models import (
    BaseRecord,
    ForecastRecord,
    SP1ForecastAromeRecord,
    SP2ForecastAromeRecord,
)


class ForecastRecordTests(unittest.TestCase):
    def test_forecast_records_share_metadata_filtering(self):
        self.assertTrue(issubclass(SP1ForecastAromeRecord, ForecastRecord))
        self.assertTrue(issubclass(SP2ForecastAromeRecord, ForecastRecord))
        self.assertEqual(
            SP1ForecastAromeRecord.forecast_variables(),
            {
                "t2m",
                "r2",
                "si10",
                "wdir10",
                "ssrd",
                "tp",
                "prmsl",
                "fg10",
                "tsnowp",
            },
        )
        self.assertEqual(
            SP2ForecastAromeRecord.forecast_variables(),
            {"lcc", "mcc", "hcc", "CAPE_INS"},
        )

    def test_api_reference_records_remain_available(self):
        for record_type in (
            BronzeObservationListeStationsRecords,
            AllSP1ForecastAromeRecords,
            AllSP2ForecastAromeRecords,
            SilverForecastAromeRecords,
        ):
            with self.subTest(record_type=record_type.__name__):
                self.assertTrue(issubclass(record_type, BaseRecord))


if __name__ == "__main__":
    unittest.main()
