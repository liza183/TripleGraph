rm -rf DB
mkdir DB
clear
echo "server started..."
#java -XX:-UseGCOverheadLimit -Xmx12G -jar fuseki-server.jar --update --mem /ds &
#java -Xmx12G -jar fuseki-server.jar --update --loc=DB /ds &
#java -Xmx12800M -jar fuseki-server.jar --update --loc=DB /ds &
java -Xms12G -Xmx14G -jar fuseki-server.jar --update --mem /ds 
