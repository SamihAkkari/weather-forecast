import unittest
from unittest.mock import MagicMock, mock_open, patch

from scripts import initialiser


class InitialiserTests(unittest.TestCase):
    def setUp(self):
        self.connection = MagicMock()
        self.cursor = MagicMock()
        self.connection.cursor.return_value.__enter__.return_value = self.cursor

    @patch("scripts.initialiser.DatabaseConnection")
    def test_create_table_executes_schema_and_table(self, connection_factory):
        connection_factory.return_value.__enter__.return_value = self.connection

        initialiser._create_table("silver", "observations", "station_id TEXT")

        self.assertEqual(
            [call.args[0] for call in self.cursor.execute.call_args_list],
            [
                "CREATE SCHEMA IF NOT EXISTS silver",
                "CREATE TABLE IF NOT EXISTS silver.observations (station_id TEXT)",
            ],
        )

    @patch("scripts.initialiser.DatabaseConnection")
    def test_create_hypertable_enables_extension_and_uses_partition_column(
        self,
        connection_factory,
    ):
        connection_factory.return_value.__enter__.return_value = self.connection

        initialiser._create_table(
            "silver",
            "forecast",
            "station_id TEXT",
            hypertable_on="run_time",
        )

        statements = [call.args[0] for call in self.cursor.execute.call_args_list]
        self.assertEqual(statements[0], "CREATE EXTENSION IF NOT EXISTS timescaledb")
        self.assertEqual(statements[1], "CREATE SCHEMA IF NOT EXISTS silver")
        self.assertIn("CREATE TABLE IF NOT EXISTS silver.forecast", statements[2])
        self.assertEqual(
            statements[3],
            "SELECT create_hypertable('silver.forecast', 'run_time', "
            "'station_id', 4, if_not_exists => TRUE)",
        )

    @patch("builtins.open", new_callable=mock_open)
    @patch("scripts.initialiser.DatabaseConnection")
    def test_station_copy_is_skipped_when_table_has_data(
        self,
        connection_factory,
        open_file,
    ):
        connection_factory.return_value.__enter__.return_value = self.connection
        self.cursor.fetchone.return_value = (1,)

        initialiser.make_stations_table("stations.csv", "bronze", "stations")

        open_file.assert_not_called()
        self.cursor.copy_expert.assert_not_called()
        connection_factory.return_value.__exit__.assert_called_once_with(
            None,
            None,
            None,
        )

    @patch("builtins.open", new_callable=mock_open)
    @patch("scripts.initialiser.DatabaseConnection")
    def test_station_copy_uses_connection_context(
        self,
        connection_factory,
        open_file,
    ):
        connection_factory.return_value.__enter__.return_value = self.connection
        self.cursor.fetchone.return_value = (0,)

        initialiser.make_stations_table("stations.csv", "bronze", "stations")

        self.cursor.copy_expert.assert_called_once_with(
            "COPY bronze.stations FROM STDIN WITH CSV HEADER DELIMITER ';'",
            open_file.return_value,
        )
        connection_factory.return_value.__exit__.assert_called_once_with(
            None,
            None,
            None,
        )


if __name__ == "__main__":
    unittest.main()
