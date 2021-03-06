echo "Restarting torrentor..."
echo "kill previous processes"
ps ax | grep redis-server | cut -c 1-5 | sudo xargs kill
ps ax | grep rtorrent | cut -c 1-5 | sudo xargs kill
ps ax | grep core.py | cut -c 1-5 | sudo xargs kill

echo "running redis"
screen -S redis  -d -m redis-server
echo "running rtorrent"
screen -S rtorrent  -d -m rtorrent
echo "running web layer"
sudo screen -S torrentor  -d -m ./core.py 
echo "running nginx" 
sudo service nginx restart
