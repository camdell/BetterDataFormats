# Better Data Formats for Faster Analysis

```python
print("Let's Take a Look!")
```

## Persisting Data

```python
from time import sleep
from utils import timed
from functools import cache

def slow_summation(x, y):
    sleep(3)
    return x + y

with timed():
    print(f"{slow_summation(4, 5) = }")

with timed():
    print(f"{slow_summation(4, 5) = }")

with timed():
    print(f"{slow_summation(4, 5) = }")
```

- Save and load data efficiently for later analysis
- Avoid repeating expensive computations
- File formats affect speed, size, and fidelity

## Text vs Binary

Actually, it’s all bytes. You can think of bytes as the substrate of data:
whether that data represents "text" or an "integer" depends entirely on how
you interpret it.

- **Text**: bytes meant to be interpreted as characters using a character
  encoding (e.g., UTF-8, Latin-1, ASCII, …)
- **Binary**: bytes meant to be interpreted according to a non-textual schema
  (e.g., fixed-width integers, IEEE-754 floats, …)

```python
from numpy import arange, savetxt, loadtxt, save, load
from pathlib import Path

data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

txt_path = data_dir / "array.txt"
bin_path = data_dir / "array.npy"

arr = arange(14)
savetxt(txt_path, arr, fmt="%d")                   # save/savetxt → serialization
save(bin_path, arr)

assert (loadtxt(txt_path) == load(bin_path)).all() # load/loadtxt → deserialization
# round tripping: the process of serializing and deserializing
```

**Serialization**: Convert in-memory objects into a storable or transmittable format.
**Deserialization**: Convert stored or transmitted data back into usable in-memory objects.

Then what is in the files?

```zsh
# cat data/array.txt
# xxd data/array.txt

cat data/array.npy
# xxd data/array.npy
```

```python
from numpy import arange, savetxt, save
from pathlib import Path

data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

txt_path = data_dir / "array.txt"
bin_path = data_dir / "array.npy"

arr = arange(1_000_000)
savetxt(txt_path, arr)
save(bin_path, arr)
print("done")
```

```zsh
du -h data/array.npy
du -h data/array.txt
```

```python
from numpy import loadtxt, load
from utils import timed
from pathlib import Path

data_dir = Path("data")

txt_path = data_dir / "array.txt" # read in 1 byte, does it correspond to a number like '1', if so then provide 1
bin_path = data_dir / "array.npy" # read in 1 byte, intrepret it as an integer

with timed("txt") as txt_time:
    loadtxt(txt_path)

with timed("npy") as bin_time:
    load(bin_path)

print(f"`load` was {txt_time() / bin_time():.3f}x faster than `loadtxt`")
```

## Tabular Data Formats

`.csv` (comma separated values; semi-structured text)

```
a,       b,       c
value1,  value2,  value3
value4,  value5,  value6
```

*Why is this layout non-optimal for computers*
- Column-wise operations inefficient (parse row strings to numbers)
- Extra bytes for delimiters, headers, and ASCII encoding
- Parsing strings adds CPU overhead

```python
from pandas import DataFrame, read_csv, date_range, concat, read_parquet

orig_df = DataFrame({'dates': date_range('2000-01-01', freq='YE', periods=6)})
orig_df.to_parquet('data/dates.parquet', index=False)
roundtrip_df = read_parquet('data/dates.parquet')

print(
    concat([orig_df, roundtrip_df], axis=1).dtypes
)
```

Other options:
`.xlsx` → structured text, compressed, preserves formatting, slower for large numeric data
`.parquet` → columnar binary, fast column operations, small file size

```
a,    b,           c
1,  2.5,  2000-01-01
4,  5.5,  2000-02-01

---

a:1,4
b:2.5,5.5
c:2000-01-01,2000-02-01
{a: int64, b: float64, c: dates}
```

Let’s Take a Look at some data

```python
from pandas import DataFrame, date_range
from pathlib import Path
from string import ascii_lowercase

import numpy as np
from numpy.random import default_rng

rng = default_rng(0)
size = 100_000

df = DataFrame({
    'a': np.arange(size),
    'b': rng.uniform(0, 5, size=size),
    'c': rng.choice([*'WXYZ'], size=size),
    'd': date_range(start='2000-01-01', freq='min', periods=size)
}).convert_dtypes(dtype_backend='pyarrow')

for i, letter in enumerate(ascii_lowercase):
    if letter in df.columns: continue
    df[letter] = i

data_dir = Path('data')
data_dir.mkdir(exist_ok=True)

df.to_csv(data_dir / 'tabular.csv', index=False)
df.to_parquet(data_dir / 'tabular.parquet', index=False)
df.to_excel(data_dir / 'tabular.xlsx', index=False)

print(df)
```

```zsh
ls data/tabular*

du -sh data/tabular.* | sort -h
```

```python
from utils import timed
from pandas import read_csv, read_excel, read_parquet

with timed('csv'):
    read_csv('data/tabular.csv')

with timed('parquet'):
    read_parquet('data/tabular.parquet', dtype_backend='pyarrow')

with timed('xlsx'):
    read_excel('data/tabular.xlsx')
```

_csv_: Easy to interact & introspect

```zsh
head -n 5 data/tabular.csv
```

_xlsx_: preserves formatting, multiple sheets, requires Excel or LibreOffice

```zsh
# head -n 5 data/tabular.xlsx
# unzip -o data/tabular.xlsx -d data/tabular
# tree data/tabular
xmllint data/tabular/xl/worksheets/sheet1.xml --format --noblanks | head -n 21
```

parquet: binary columnar format, optimized for large numeric/tabular datasets

```zsh
# xxd data/tabular.parquet | head -n 20
# parquet-tools show data/tabular.parquet --head 5
parquet-tools inspect data/tabular.parquet
```

**Why Parquet is fast & compact**

- Columnar storage → read only needed columns
- Binary encoding → no string parsing
- Compression-friendly → smaller disk footprint
- Preserves exact numeric types → no rounding

## Semi Structured Formats

- JSON → human-readable, hierarchical, slower for numeric-heavy data
- Thrift → binary, compact, schema-enforced, fast serialization/deserialization

```python
import json

people = [
    {'name': 'Alice',    'age': 20},
    {'name': 'Bob',      'age': 21},
    {'name': 'Charlie',  'age': 22},
    {'name': 'Dana',     'age': 23},
]

with open('data/people.json', 'w') as f:
    json.dump(people, f)

print(json.dumps(people))
```

```zsh
# cat data/people.json

jq '.[0].name' data/people.json
```

Thrift

```python
import thriftpy2
from thriftpy2.protocol import TBinaryProtocol
from thriftpy2.transport import TMemoryBuffer
from io import StringIO
from textwrap import dedent

# {'name': 'Alice', 'id': 1}
buffer = StringIO(
    dedent("""
        struct Person {
          1: string name
          2: i32 id
        }

        struct People {
          1: list<Person> persons
        }
    """).lstrip()
)

people_thrift = thriftpy2.load_fp(buffer, module_name="people_thrift")
people = people_thrift.People(persons=[
    people_thrift.Person(name='Alice',   id=0),
    people_thrift.Person(name='Bob',     id=1),
    people_thrift.Person(name='Charlie', id=2),
    people_thrift.Person(name='Dana',    id=3),
])

# Serialize to binary file
buf = TMemoryBuffer()
proto = TBinaryProtocol(buf)
people.write(proto)

with open("data/people.thrift", "wb") as f:
    f.write(buf.getvalue())
```

```zsh
xxd data/people.thrift
```

**Strengths of text-based formats**
- Human-readable and editable with any text editor
- Easier to debug and inspect without specialized tools
- Language-agnostic and highly portable
- Can be compressed effectively if needed (e.g., CSV → gzip)
- Often simpler for small datasets or logs

**Strengths of binary formats**
- Exact representation of numeric values (no rounding errors)
- Much faster to read and write for large datasets
- Smaller file sizes for equivalent data (no ASCII encoding overhead)
- Can readily store complex data structures directly (arrays, structs, nested data)
