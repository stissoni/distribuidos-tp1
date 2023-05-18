class Row:
    def __init__(self, table, fields, values) -> None:
        if len(fields) != len(values):
            raise Exception("Number of fields does not match number of values")

        self.table = table
        self.fields = fields
        self.values = values

    # Generate string representation of row
    def __str__(self) -> str:
        row = [f"{self.fields[i]}={self.values[i]}" for i in range(len(self.values))]
        row = ",".join(row)
        return row
