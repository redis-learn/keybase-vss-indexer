import os

import numpy as np
import redis
from bs4 import BeautifulSoup
from markdown import markdown
from sentence_transformers import SentenceTransformer

# Initialization
model = SentenceTransformer('sentence-transformers/all-distilroberta-v1')

# Unmanaged, let's crash the service if no connection
r = redis.StrictRedis(host=os.getenv('DB_SERVICE', '127.0.0.1'),
                      port=int(os.getenv('DB_PORT', 6379)),
                      password=os.getenv('DB_PWD', ''),
                      db=0,
                      ssl=os.getenv('DB_SSL', False),
                      ssl_keyfile=os.getenv('DB_SSL_KEYFILE', ''),
                      ssl_certfile=os.getenv('DB_SSL_CERTFILE', ''),
                      ssl_ca_certs=os.getenv('DB_CA_CERTS', ''),
                      ssl_cert_reqs=os.getenv('DB_CERT_REQS', ''),
                      decode_responses=os.getenv('DB_DECODE_RESPONSE', True))

# Create consumer group and stream altogether
try:
    r.xgroup_create("keybase:events", "vss_readers", id='$', mkstream=True)
except redis.exceptions.ResponseError:
    print("the consumer group likely exists")


def process_event(message_id, pk):
    print("vss processing for document " + pk)
    document = r.json().get('keybase:json:{}'.format(pk),
                            '$.currentversion',
                            '$.privacy',
                            '$.state')
    current = document['$.currentversion'][0]

    # Markdown to text
    html = markdown(current['content'])
    soup = BeautifulSoup(html, "html.parser")
    content = soup.get_text()

    # Generate embedding
    embedding = model.encode(content).astype(np.float32).tobytes()
    doc = {"content_embedding": embedding,
           "name": current['name'],
           "state": document['$.state'][0],
           "privacy": document['$.privacy'][0]}
    r.hset("keybase:vss:{}".format(pk), mapping=doc)

    r.xack("keybase:events", "vss_readers", message_id)


while True:
    # events reads as [['keybase:events', [('1681393555441-0', {'type': 'publish', 'id': 'weovoo488q'})]]]
    ev = r.xreadgroup('vss_readers', 'default', {'keybase:events': '>'}, count=1, block=10000)
    if len(ev) != 0:
        print("found event...")
        process_event(ev[0][1][0][0], ev[0][1][0][1]['id'])
    else:
        # Check if there is something pending
        # claimed reads as ['1681391854729-0', [('1681391822826-0', {'type': 'publish', 'id': '1nh53wraw9'})]]
        ev = r.xautoclaim('keybase:events', 'vss_readers', 'default', 10000, count=1, start_id='0')
        if len(ev[1]) != 0:
            print("claiming...")
            process_event(ev[1][0][0], ev[1][0][1]['id'])
        else:
            print("nothing to do here...")
