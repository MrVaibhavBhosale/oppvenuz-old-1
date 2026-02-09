from .settings import *

STATIC_URL = '/static/'
STATIC_ROOT = '/vol/web/static'
# logger
LOGGING_DIR = '/var/log'

logging_structure = {

      'debug_logs' : {
             'dir' : '/debug_logs',
             'file': '/debug.log'
      } ,
            'warning_logs': {
             'dir' : '/warning_logs',
             'file': '/warning.log'
      },
            'error_logs': {
             'dir' : '/error_logs',
             'file': '/error.log'
      },
            'info_logs': {
             'dir' : '/info_logs',
             'file': '/info.log'
      },
            'critical_logs': {
             'dir' : '/critical_logs',
             'file': '/critical.log'
      }

}

for key, value in logging_structure.items():
        log_dir = LOGGING_DIR + value['dir']
        os.makedirs(log_dir,exist_ok=True)
        open(log_dir+value['file'],'a').close()

LOGGING = {
   'version': 1,
   'disable_existing_loggers': False,
   'formatters': {
       'standard': {
           'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
       },
   },
   'handlers': {
       'debug': {
           'level': 'DEBUG',
           'class': 'logging.handlers.RotatingFileHandler',
           'filename': os.path.join(LOGGING_DIR, 'debug_logs/debug.log'),
           'backupCount': 10,  # keep at most 10 log files
           'maxBytes': 5242880,  # 5*1024*1024 bytes (5MB)
           'formatter': 'standard',
       },
       'warning': {
           'level': 'WARNING',
           'class': 'logging.handlers.RotatingFileHandler',
           'filename': os.path.join(LOGGING_DIR, 'warning_logs/warning.log'),
           'backupCount': 10, # keep at most 10 log files
           'maxBytes': 5242880, # 5*1024*1024 bytes (5MB)
           'formatter': 'standard',
       },
       'error': {
           'level': 'ERROR',
           'class': 'logging.handlers.RotatingFileHandler',
           'filename': os.path.join(LOGGING_DIR, 'error_logs/error.log'),
           'backupCount': 10,  # keep at most 10 log files
           'maxBytes': 5242880,  # 5*1024*1024 bytes (5MB)
           'formatter': 'standard',
       },
       'info': {
           'level': 'INFO',
           'class': 'logging.handlers.RotatingFileHandler',
           'filename': os.path.join(LOGGING_DIR, 'info_logs/info.log'),
           'backupCount': 10,  # keep at most 10 log files
           'maxBytes': 5242880,  # 5*1024*1024 bytes (5MB)
           'formatter': 'standard',
       },
       'critical_logs': {
           'level': 'CRITICAL',
           'class': 'logging.handlers.RotatingFileHandler',
           'filename': os.path.join(LOGGING_DIR, 'critical_logs/critical.log'),
           'backupCount': 10,  # keep at most 10 log files
           'maxBytes': 5242880,  # 5*1024*1024 bytes (5MB)
           'formatter': 'standard',
       },
   },
   'loggers': {
       'django': {
           'handlers': ['debug', 'warning', 'error', 'info', 'critical_logs'],
           'level': 'DEBUG',
           'propagate': True,
       },
   },
}
