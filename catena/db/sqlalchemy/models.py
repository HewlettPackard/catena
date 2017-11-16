# (C) Copyright 2017 Hewlett Packard Enterprise Development LP.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Catena Models!
"""

import json
import uuid

from oslo_db.sqlalchemy import enginefacade
from oslo_db.sqlalchemy import models
from oslo_serialization import jsonutils
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy.orm import relationship
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.types import TypeDecorator

from catena.common import utils
from catena.common.utils import decrypt_private_rsakey

BASE = declarative_base()


class JSONEncodedDict(TypeDecorator):
    """Represents an immutable structure as a json-encoded string"""

    impl = Text

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = jsonutils.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = jsonutils.loads(value)
        return value


class CatenaBase(models.ModelBase, models.TimestampMixin):
    """Base class for Glance Models."""

    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    __table_initialized__ = False
    __protected_attributes__ = set(
        [
            "created_at",
            "updated_at",
            "deleted_at",
            "deleted"
        ]
    )

    @enginefacade.writer
    def save(self, context):
        super(CatenaBase, self).save(context.session)

    created_at = Column(
        DateTime,
        default=lambda: utils.utcnow(),
        nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: utils.utcnow(),
        nullable=True,
        onupdate=lambda: utils.utcnow())
    deleted_at = Column(DateTime)
    deleted = Column(Boolean, nullable=False, default=False)

    @enginefacade.writer
    def delete(self, context):
        context.session.delete(self)

    def keys(self):
        return self.__dict__.keys()

    def values(self):
        return self.__dict__.values()

    def items(self):
        return self.__dict__.items()

    def to_dict(self):
        d = self.__dict__.copy()
        # NOTE(flaper87): Remove
        # private state instance
        # It is not serializable
        # and causes CircularReference
        d.pop("_sa_instance_state")
        return d


class Chain(BASE, CatenaBase):
    """Represents an image in the datastore."""
    __tablename__ = 'chains'
    __table_args__ = (
        Index('ix_chain_deleted', 'deleted'),
        Index('owner_chain_idx', 'owner'),
        Index('created_at_chain_idx', 'created_at'),
        Index('updated_at_chain_idx', 'updated_at'),
        {
            'mysql_engine': 'InnoDB',
            'mysql_charset': 'utf8'
        }
    )

    id = Column(String(36),
                primary_key=True,
                default=lambda: str(uuid.uuid4()))
    name = Column(String(255))

    chain_backend = Column(
        Enum(
            'ethereum',
            'ripple',
            name='chain_backend'),
        nullable=False)

    cloud_id = Column(String(36), ForeignKey('clouds.id'), nullable=False)
    cloud = relationship('Cloud')

    nodes = relationship(
        'ChainNodes',
        back_populates='chain',
        cascade="all, delete, delete-orphan")

    cloud_config = Column(Text())
    chain_config = Column(Text())

    status = Column(String(30), nullable=False)
    owner = Column(String(255))

    def get_chain_config(self):
        return json.loads(self.chain_config)

    def get_cloud_config(self):
        return json.loads(self.cloud_config)

    def set_chain_config(self, chain_config):
        self.chain_config = json.dumps(chain_config)

    def set_cloud_config(self, cloud_config):
        self.cloud_config = json.dumps(cloud_config)


class ChainNodes(BASE, CatenaBase):
    """Represents an image properties in the datastore."""
    __tablename__ = 'chain_nodes'

    id = Column(String(36),
                primary_key=True,
                default=lambda: str(uuid.uuid4()))

    name = Column(String(255))

    chain_id = Column(String(36), ForeignKey('chains.id'), nullable=False)

    chain = relationship('Chain', back_populates='nodes')

    type = Column(Text())

    chain_config = Column(Text())

    ssh_key = Column(Text())
    ip = Column(String(16), nullable=False)

    def get_ssh_key(self, file):
        return decrypt_private_rsakey(self.ssh_key, file)

    def get_chain_config(self):
        if self.chain_config:
            return json.loads(self.chain_config)
        else:
            return {}

    def set_chain_config(self, chain_config):
        self.chain_config = json.dumps(chain_config)


class Cloud(BASE, CatenaBase):
    """Represents a cloud in the datastore"""
    __tablename__ = 'clouds'

    id = Column(String(36),
                primary_key=True,
                default=lambda: str(uuid.uuid4())
                )

    type = Column(Text())
    name = Column(Text())

    authentication = Column(Text())
    cloud_config = Column(Text())

    def get_authentication(self):
        return json.loads(self.authentication)

    def set_authentication(self, authentication):
        self.authentication = json.dumps(authentication)

    def get_cloud_config(self):
        return json.loads(self.cloud_config)

    def set_cloud_config(self, cloud_config):
        self.cloud_config = json.dumps(cloud_config)


@enginefacade.writer
def register_models(context):
    """Create database tables for all models with the given engine."""
    models = (Chain, ChainNodes, Cloud)
    for model in models:
        model.metadata.create_all(context)


@enginefacade.writer
def unregister_models(context):
    """Remove database tables for all models with the given engine."""
    models = (Chain, ChainNodes, Cloud)
    for model in models:
        model.metadata.drop_all(context)
