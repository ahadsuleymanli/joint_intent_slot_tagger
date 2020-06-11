import numpy as np 
import pandas as pd 

LENGTH = 4
COLS = 4
ROWS = 6

alphabet = list('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
np_alphabet = np.array(alphabet, dtype="|U1")
arr = []
for row in range(ROWS):
    np_codes = np.random.choice(np_alphabet, [COLS, LENGTH])
    codes = ["".join(np_codes[i]) for i in range(len(np_codes))]
    arr.append(codes)
arr = np.array(arr)

s = pd.Series([1,3,4,5,np.nan, 6,8,8])
dates = pd.date_range('20130101',periods=6)
df = pd.DataFrame(np.random.randn(6,4), index=dates, columns=list('ABCD'))

df2 = pd.DataFrame({'A': 1.,
   'C': pd.Series(1, index=list(range(4)), dtype='float32'),
   'D': np.array([3] * 4, dtype='int32'),
   'E': pd.Categorical(["test", "train", "test", "train"]),
   'F': 'foo'})

s = pd.DataFrame(np.array([[1, 3, 5, np.nan,7] for x in range(6) ]), index=dates, columns=list('ABCDE')).shift(1,axis=1)
x = [[1, 3, 5, np.nan,7] for x in range(6) ]
s1 = pd.Series([1, 2, 3, 4, 5, 6], index=pd.date_range('20130102', periods=6).shift(2))
df["F"] = s1

print(df)

