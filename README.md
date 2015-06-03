# Acrylic

Acrylic makes manipulating tabular ("table-shaped") data easy with an elegant,
readable syntax.

```python
from acrylic import DataTable

data = DataTable.fromcsv("sales_data.csv")
data.wheregreater("price", 20).where("category", "electronics")


```

- To jump in, view the [Quick Start](https://github.com/emlazzarin/acrylic/blob/master/docs/QUICKSTART.rst) guide.