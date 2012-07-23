

TEMPFILE=backend_log_excerpt.txt

> $TEMPFILE
tail  -f /home/jvicenik/devel/bigone_fred_root/root/var/log/fred.log | grep "generated select SQL =" | cut -d ']' -f 5- > $TEMPFILE &
sleep 3
python test_request_tweak1.py
sleep 1
python test_request_tweak2.py
sleep 1
python test_request_tweak3.py
sleep 10

kill %1
