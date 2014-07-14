# Scrapy settings for vivo_2014 project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'vivo_2014'

SPIDER_MODULES = ['vivo_2014.spiders']
NEWSPIDER_MODULE = 'vivo_2014.spiders'

EXPORT_FIELDS = ["name", "title", "position", "email", "phone", "web"]

REDIRECT_ENABLED = True

ITEM_PIPELINES = {
    "vivo_2014.pipelines.Url2IdPipeline": 100,
    "vivo_2014.pipelines.OrganizationAssignmentPipeline": 150,
    "vivo_2014.pipelines.Item2RDFPipeline": 800
}


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'vivo_2014 (+http://www.yourdomain.com)'

# TODO Accept-header for german as preferred language
