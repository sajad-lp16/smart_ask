import os
import logging.config

from core import BASE_DIR

# Create logs directory
log_dir = BASE_DIR / "logs"
os.makedirs(log_dir, exist_ok=True)

# Define the logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s'
        }
    },
    'handlers': {
        'api_file': {
            'class': 'logging.FileHandler',
            'level': 'INFO',
            'formatter': 'standard',
            'filename': os.path.join(log_dir, f'api.log'),
            'mode': 'a'
        },
        'elastic_file': {
            'class': 'logging.FileHandler',
            'level': 'ERROR',
            'formatter': 'detailed',
            'filename': os.path.join(log_dir, f'elastic.log'),
            'mode': 'a'
        },
        'database_file': {
            'class': 'logging.FileHandler',
            'level': 'INFO',
            'formatter': 'standard',
            'filename': os.path.join(log_dir, f'database.log'),
            'mode': 'a'
        },
        'update_tickets_file': {
            'class': 'logging.FileHandler',
            'level': 'INFO',
            'formatter': 'standard',
            'filename': os.path.join(log_dir, f'update_tickets.log'),
            'mode': 'a'
        },
        'mattermost_bot_file': {
            'class': 'logging.FileHandler',
            'level': 'INFO',
            'formatter': 'detailed',
            'filename': os.path.join(log_dir, f'mattermost_bot.log'),
            'mode': 'a'
        },
        'ai_file': {
            'class': 'logging.FileHandler',
            'level': 'INFO',
            'formatter': 'detailed',
            'filename': os.path.join(log_dir, f'ai.log'),
            'mode': 'a'
        },
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout'
        }
    },
    'loggers': {
        'api': {
            'handlers': ['api_file', 'console'],
            'level': 'INFO',
            'propagate': False
        },
        'elastic': {
            'handlers': ['elastic_file', 'console'],
            'level': 'ERROR',
            'propagate': False
        },
        'database': {
            'handlers': ['database_file', 'console'],
            'level': 'INFO',
            'propagate': False
        },
        'update_tickets': {
            'handlers': ['update_tickets_file', 'console'],
            'level': 'INFO',
            'propagate': False
        },
        'mattermost_bot': {
            'handlers': ['mattermost_bot_file', 'console'],
            'level': 'INFO',
            'propagate': False
        },
        'ai': {
            'handlers': ['ai_file', 'console'],
            'level': 'INFO',
            'propagate': False
        }
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO'
    }
}

# Configure logging
logging.config.dictConfig(LOGGING_CONFIG)

# Create logger instances
api_logger = logging.getLogger('api')
update_tickets_logger = logging.getLogger('update_tickets')
elastic_logger = logging.getLogger('elastic')
db_logger = logging.getLogger('database')
mattermost_bot_logger = logging.getLogger('mattermost_bot')
ai_logger = logging.getLogger('ai')
