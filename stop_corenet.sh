APT_ID=$(ps ax | grep -m1 "python db_core.py" | awk '{printf "%s",$1; }')
kill $APT_ID
APT_ID=$(ps ax | grep -m1 "python evaluate.py" | awk '{printf "%s",$1; }')
kill $APT_ID
APT_ID=$(ps ax | grep -m1 "python collector.py" | awk '{printf "%s",$1; }')
kill $APT_ID
APT_ID=$(ps ax | grep -m1 "python executor.py" | awk '{printf "%s",$1; }')
kill $APT_ID