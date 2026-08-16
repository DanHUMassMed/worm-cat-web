sudo dnf install git -y
sudo dnf install make -y
sudo dnf groupinstall -y "Development Tools"

# ===================================================
# Old Wormcat
sudo dnf install -y R R-devel

sudo dnf install -y \
    freetype-devel \
    openssl-devel \
    libcurl-devel \
    cairo-devel \
    libxml2-devel \
    git

sudo dnf install libuv-devel -y
sudo dnf install fribidi-devel -y

sudo dnf install -y \
    libpng-devel \
    libtiff-devel \
    libjpeg-turbo-devel \
    libwebp-devel \
    pkgconf-pkg-config

sudo dnf install -y libgit2-devel libssh2-devel openssl-devel

sudo R
options(repos = c(CRAN = "https://cloud.r-project.org/"))
update.packages(ask = FALSE)
install.packages(c("argparse", "data.table", "knitr", "curl", "ggplot2", "git2r", "httr", "devtools"))
install.packages(c('usethis', 'fs', 'miniUI', 'pkgdown', 'pkgload', 'profvis', 'roxygen2', 'testthat'))
library(devtools)

install_github("trinker/plotflow")
install_github("dphiggs01/wormcat")

# ===================================================
# New Wormcat3
sudo dnf install nginx -y
sudo systemctl enable nginx

curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
source ~/.bashrc && nvm install --lts

curl https://checkip.amazonaws.com

sudo ln -s /etc/nginx/sites-available/test.wormcat3.com /etc/nginx/sites-enabled/test.wormcat3.com
sudo ln -s /etc/nginx/sites-available/wormcat.com /etc/nginx/sites-enabled/wormcat.com
sudo nginx -t
sudo systemctl reload nginx


Suncoast released in 2024

http://test.ilandapps.com/


