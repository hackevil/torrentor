echo "      Welcome to Torrentor.v2 installer      "
echo "---------------------------------------------"
echo "Trying to install prerequisites       "
echo ""
echo '$1'
./install_prereq.sh
echo "Finished. Now setting up config files...   "
echo ""
python config.py '$1' 'pi' 
echo "Finished. Running services...        "
echo "Finished. If you haven't done already,"
echo "update your server settings for fcgi handling."
echo ""
./runapps.sh
echo ""
echo "---------------------------------------------"
echo "For more info: gitub.com/hgeg/torrentor   "
