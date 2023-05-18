class Message:
    def __init__(self, message_type, table, rows) -> None:
        # Check if the parameters are allowed values
        if message_type not in ["stream_data", "end_stream"]:
            raise ValueError("Invalid message type")
        if table not in [
            "montreal/weather",
            "montreal/station",
            "montreal/trip",
            "toronto/station",
            "toronto/weather",
            "toronto/trip",
            "washington/station",
            "washington/weather",
            "washington/trip",
        ]:
            raise ValueError("Invalid table")
        self.message_type = message_type
        self.table = table
        self.rows = rows

    def __str__(self) -> str:
        if self.table is not None:
            return f"type={self.message_type},table={self.table}|message={self.rows}"
        else:
            return f"type={self.message_type}|message={self.rows}"

    @staticmethod
    def from_string(self, message):
        header = message.split("|")[0]
        try:
            self.message_type = header.split(",")[0].split("=")[1]
            self.table = header.split(",")[1].split("=")[1]
        except IndexError:
            self.message_type = header.split(",")[0].split("=")[1]
            self.table = None
        self.rows = message.split("|")[1:]

    def get_message_type(self) -> str:
        return self.message_type

    def get_table(self) -> str:
        return self.table

    def get_rows_values(self) -> list:
        return [field.split("=") for field in self.rows.split(",")]
