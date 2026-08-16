To install on EC2 follow the below guidelines:
1. Create a free micro instance
    I'm using Ubuntu Server 16.04 LTS (HVM), SSD Volume Type
    expose port 9000 for gunicorn
    22 (SSH), 80 (HTTP), 443 (HTTPS), 3389 (RDP, optional), and 8787 (RStudio Server).

    add an elastic ip (in case we need to dump this instance but dont want to change IP's)

2. Start the instance and login with ssh
   * `ssh -i "PRIVATE-key.pem" ubuntu@xxx.xxx.xxx.xxx` (Provide your own permissions file and IP)
   * `sudo apt-get update`
   * `sudo apt-get -y upgrade`
   * `sudo apt-get -y install python3-pip python3-dev`
   * `sudo apt-get -y install python3-venv`
   * `pip3 install --upgrade pip setuptools`

3. Create a virtual environment for our project
   * `mkdir ~/Applications`
   * `python3 -m venv Applications/python_envs`
   * `source ~/Applications/python_envs/bin/activate`
   * `pip install --upgrade pip`
   * `pip install wheel`
   * `pip install flask`
   * `pip install flask-wtf`
   * `pip install gunicorn`
   * `pip install gevent`
   
    * `pip install pandas`
    * `pip install werkzeug==0.16.1`
    * `pip install celery`
    * `pip install redis`
    * `pip install redis-py`
    * `pip install xlrd`
    * `pip install xlsxwriter`

4. clone project to the EC2 Instance
   * `cd ~/Applications`
   * `cd ~/Applications/worm_cat;kill -9 `cat gunicorn.pid`;cd ..;rm -rf worm_cat ` (If you are upgrading; first remove the old instance of wormcat.)
   * `git clone https://github.com/dphiggs01/worm-cat-web.git`
   * `source ~/Applications/python_envs/bin/activate`
   * `cd worm_cat;nohup ./run.sh &`

5. Check the running web app
   * visit http://xxx.xxx.xxx.xxx:9000/ (run.sh defaults to port 9000)


   for d in `ps -auxww|grep python|cut -d' ' -f4`;do echo $d; done
   kill -9 `cat thermo_ui/gunicorn.pid`

6. Install R
   * `sudo echo "deb http://cran.rstudio.com/bin/linux/ubuntu bionic-cran35/" | sudo tee -a /etc/apt/sources.list`
   * `sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 51716619E084DAB9`
   * `sudo apt-get update`
   * `sudo apt-get upgrade`
   * `sudo apt-get install libfreetype6-dev`
   * `sudo apt-get install r-base r-base-dev`
   * `sudo apt-get install libssl-dev libcurl4-openssl-dev `
   * `sudo apt-get install libcairo2-dev`
   * `sudo apt-get install build-essential libcurl4-gnutls-dev libxml2-dev`
   

7. Install R Packages
   * `R` --Start R
   * `options("repos" = c(CRAN = "http://cran.rstudio.com/"))`
   * `old.packages()` -- list all packages where an update is available
   * `update.packages()` -- update all available packages
   * `install.packages(c("argparse","data.table", "knitr", "curl","ggplot2","git2r","httr","devtools"))`

   * `library("devtools")`
   * `install_github("trinker/plotflow")`
   * `install_github("dphiggs01/wormcat")`


8. Install rstudio-server (Note RStudio is NOT required)
   * `sudo adduser rstudio`
   * `sudo echo "deb https://cloud.r-project.org/bin/linux/ubuntu xenial/" | sudo tee -a /etc/apt/sources.list`
   * `sudo echo "deb http://mirror.math.princeton.edu/pub/ubuntu/ xenial main bionic-backports restricted universe" | sudo tee -a /etc/apt/sources.list`
   * `sudo apt-get update`
   * `sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 51716619E084DAB9`
   * `sudo apt-get install gdebi-core`
   * `wget https://download2.rstudio.org/rstudio-server-1.1.453-amd64.deb`
   * `sudo gdebi rstudio-server-1.1.453-amd64.deb`


9. Stop and Start rstudio-server
   * `sudo rstudio-server status`
   * `sudo rstudio-server stop`
   * `sudo rstudio-server start`

10. test connection
   * visit http://xxx.xxx.xxx.xxx:8787/
