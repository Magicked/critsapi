import datetime
import logging

from bson.objectid import ObjectId
from pymongo import MongoClient

log = logging.getLogger()


class CRITsDBAPI():
    """
    Interface to the raw CRITs mongodb backend. This is typically much faster
    than using the provided web API.

    Most queries require a "collection" variable. The is the mongodb
    collection for the TLO in CRITs. It must follow the specific mongo
    collection name for the corresponding TLO. The following are acceptable:
        - indicators
        - sample
        - events
        - backdoors
        - exploits
        - domains
        - ips
    """

    def __init__(self,
                 mongo_host='localhost',
                 mongo_port=27017,
                 mongo_user='',
                 mongo_pass='',
                 db_name='crits'):
        """
        Create our CRITsDBAPI object.

        Args:
            mongo_host: The server name/ip where the mongo db is hosted
            mongo_port: The port listening for connections
            mongo_user: Mongo username (if using)
            mongo_pass: Password for the user (if using)
            db_name: The name of the CRITs database.
        """
        # Build the authentication portion. Simple authentication only for now.
        auth_str = ''
        if mongo_user != '':
            auth_str = mongo_user
        if mongo_pass != '' and mongo_user != '':
            auth_str = auth_str + ':' + mongo_pass
        if auth_str != '':
            auth_str = auth_str + '@'
        # Build the URI
        self.mongo_uri = 'mongodb://{}{}:{}'.format(auth_str, mongo_host,
                                                    mongo_port)
        self.db_name = db_name
        self.client = None
        self.db = None

    def connect(self):
        """
        Starts the mongodb connection. Must be called before anything else
        will work.
        """
        self.client = MongoClient(self.mongo_uri)
        self.db = self.client[self.db_name]

    def find(self, collection, query):
        """
        Search a collection for the query provided. Just a raw interface to
        mongo to do any query you want.

        Args:
            collection: The db collection. See main class documentation.
            query: A mongo find query.
        Returns:
            pymongo Cursor object with the results.
        """
        obj = getattr(self.db, collection)
        result = obj.find(query)
        return result

    def find_one(self, collection, query):
        """
        Search a collection for the query provided and return one result. Just
        a raw interface to mongo to do any query you want.

        Args:
            collection: The db collection. See main class documentation.
            query: A mongo find query.
        Returns:
            pymongo Cursor object with the results.
        """
        obj = getattr(self.db, collection)
        result = obj.find_one(query)
        return result

    def add_embedded_campaign(self, id, collection, campaign, confidence,
                              analyst, date, description):
        """
        Adds an embedded campaign to the TLO.

        Args:
            id: the CRITs object id of the TLO
            collection: The db collection. See main class documentation.
            campaign: The campaign to assign.
            confidence: The campaign confidence
            analyst: The analyst making the assignment
            date: The date of the assignment
            description: A description
        Returns:
            The resulting mongo object
        """
        if type(id) is not ObjectId:
            id = ObjectId(id)
        # TODO: Make sure the object does not already have the campaign
        # Return if it does. Add it if it doesn't
        obj = getattr(self.db, collection)
        result = obj.find({'_id': id, 'campaign.name': campaign})
        if result.count() > 0:
            return
        else:
            log.debug('Adding campaign to set: {}'.format(campaign))
            campaign_obj = {
                'analyst': analyst,
                'confidence': confidence,
                'date': date,
                'description': description,
                'name': campaign
            }
            result = obj.update(
                {'_id': id},
                {'$push': {'campaign': campaign_obj}}
            )
            return result

    def add_bucket_list_item(self, id, collection, item):
        """
        Adds an item to the bucket list

        Args:
            id: the CRITs object id of the TLO
            collection: The db collection. See main class documentation.
            item: the bucket list item to add
        Returns:
            The mongodb result
        """
        if type(id) is not ObjectId:
            id = ObjectId(id)
        obj = getattr(self.db, collection)
        result = obj.update(
            {'_id': id},
            {'$addToSet': {'bucket_list': item}}
        )
        return result