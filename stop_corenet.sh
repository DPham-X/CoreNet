kill $(ps aux | grep "[g]unicorn" | awk '{print $2}')
kill $(ps aux | grep "[p]ython evaluate.py"   | awk '{print $2}')
kill $(ps aux | grep "[p]ython collector.py"  | awk '{print $2}')
kill $(ps aux | grep "[p]ython executor.py"   | awk '{print $2}')
