



class MailServerHandler(BaseHandler):

    executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

    @tornado.concurrent.run_on_executor
    def create_server(self, host, prt, usern, passwd, sendr, owner_pseudo=None):
        """
            create_server :: Self
                          -> String               -- ^ smtp hostname
                          -> Int                  -- ^ smtp port
                          -> String               -- ^ smtp username
                          -> String               -- ^ smtp password
                          -> String               -- ^ identity email
                          -> Maybe String         -- ^ owner pseudo
                          -> IO Map String String -- ^ request info
            ========================================================
            This method creates a new mail_server given proper infos
        """
        ret = {}
        ret_code = HTTP_OK

        if owner_pseudo is not None:
            owner = self.ormdb.query(User).filter_by(pseudo=owner_pseudo).first()

        serv = MailServer(host, prt, usern, passwd, sendr, owner)

        try:
            self.ormdb.add(serv)
            self.ormdb.flush()
            ret = serv.to_dict()
            self.ormdb.commit()

        except exc.IntegrityError as e:
            ret_code = HTTP_BAD_REQUEST
            ret = { 'error': 'mail_server already exists' }
        except Exception as e:
            logger.exception('Unhandled Exception')
            ret_code = HTTP_BAD_REQUEST
            ret = { 'error': 'Unhandled Exception' }

        return (ret, ret_code)

    @tornado.concurrent.run_on_executor
    def update_server(self, host, usern, prt=None, passwd=None, sendr=None,
                      owner_pseudo=None):
        """
            update_server :: Self
                          -> String               -- ^ hostname of server
                          -> String               -- ^ username of server
                          -> Maybe Int            -- ^ new port
                          -> Maybe String         -- ^ new password
                          -> Maybe String         -- ^ new identity
                          -> Maybe String         -- ^ owner pseudo
                          -> IO Map String String -- ^ request info
            ======================================================
            This function updates a mail_server object in database
        """
        ret = {}
        ret_code = HTTP_OK

        srv = self.ormdb.query(MailServer) \
                        .filter_by(hostname=host, username=usern).first()
        if srv is not None:
            try:
                if passwd is not None:
                    #keyring.set_password(srv.hostname, srv.username, passwd)
                    srv.password = passwd

                if prt is not None:
                    srv.port = prt

                if sendr is not None:
                    srv.sender = sendr

                if owner_pseudo is not None:
                    owner = self.ormdb.query(User) \
                                      .filter_by(pseudo=owner_pseudo).first()
                    if owner is None:
                        ret_code = HTTP_NOT_FOUND
                        ret = { 'error': 'owner does not exist' }
                    else:
                        srv.owner = owner

                ret = srv.to_dict()
                self.ormdb.commit()

            except Exception as e:
                logger.exception('user could not be updated')
                ret_code = HTTP_BAD_REQUEST
                ret = { 'error': 'user could not be updated' }
        else:
            ret_code = HTTP_BAD_REQUEST
            ret = { 'error': 'mail_server does not exist' }

        return (ret, ret_code)

    @tornado.gen.coroutine
    def get(self):
        ret = {}
        ret_code = HTTP_OK
        dp=True
        try:
            host = self.get_argument('hostname')
            usern = self.get_argument('username')

            uniq_redis_id = 'mail_servers_{0}{1}_{2}' \
                               .format(host, usern, STATIC_CACHID)
            red_res = self.redis.get(uniq_redis_id)
            if red_res is not None:
                ret = red_res
                dp=False
            else:
                us = self.ormdb.query(MailServer) \
                               .filter_by(hostname=host, username=usern).first()
                if us is not None:
                    ret = us.to_dict()
                    self.redis.set(uniq_redis_id, json.dumps(ret, indent=4))
                    self.redis.expire(uniq_redis_id, REDIS_CACHE_TIMEOUT)
                else:
                    ret_code = HTTP_NOT_FOUND
                    ret = { 'error': 'inexistant object for hostname/username pair' }

        except tornado.web.MissingArgumentError as e:
            ret_code = HTTP_BAD_REQUEST
            ret = { 'error': 'hostname and username must be provided' }

        self.respond(ret, ret_code, data_dump=dp)

    @tornado.gen.coroutine
    def post(self):
        ret = {}
        ret_code = HTTP_OK
        try:
            host         = self.get_argument('hostname')
            prt          = self.get_argument('port')
            passwd       = self.get_argument('password')
            usern        = self.get_argument('username')
            sendr        = self.get_argument('mail_sender')
            owner_pseudo = self.get_argument('owner', default=None)

            prt2 = int(prt)
            if not (prt2 in [25, 465, 587]):
                raise ValueError

            ret, ret_code = yield self.create_server(host, prt2, usern,
                                                     passwd, sendr, owner_pseudo)

        except tornado.web.MissingArgumentError:
            ret_code = HTTP_BAD_REQUEST
            ret = { 'error': 'post form is missing required data' }
        except ValueError:
            ret_code = HTTP_BAD_REQUEST
            ret = { 'error': 'port must be 25, 465 or 587' }

        self.respond(ret, ret_code)

    @tornado.gen.coroutine
    def put(self):
        ret = {}
        ret_code = HTTP_OK
        try:
            host         = self.get_argument('hostname')
            usern        = self.get_argument('username')
            prt          = self.get_argument('port', default=None)
            passwd       = self.get_argument('password', default=None)
            sendr        = self.get_argument('mail_sender', default=None)
            owner_pseudo = self.get_argument('owner', default=None)

            prt2=None
            if prt is not None:
                prt2 = int(prt)
                if not (prt2 in [25, 465, 587]):
                    raise ValueError

            ret, ret_code = yield self.update_server(host, usern, prt2,
                                                     passwd, sendr, owner_pseudo)
            if ret_code == HTTP_OK:
                uniq_redis_id = 'mail_servers_{0}{1}_{2}' \
                                   .format(host, usern, STATIC_CACHID)
                self.redis.set(uniq_redis_id, json.dumps(ret, indent=4))
                self.redis.expire(uniq_redis_id, REDIS_CACHE_TIMEOUT)

        except tornado.web.MissingArgumentError as e:
            ret_code = HTTP_BAD_REQUEST
            ret = { 'error': 'put form is missing required data' }
        except ValueError:
            ret_code = HTTP_BAD_REQUEST
            ret = { 'error': 'port must be 25, 465 or 587' }

        self.respond(ret, ret_code)

    @tornado.gen.coroutine
    def delete(self):
        ret = {}
        ret_code = HTTP_OK
        try:
            username = self.get_argument('pseudo')
            us = self.ormdb.query(User).filter_by(pseudo=username).first()
            if us is not None:
                self.ormdb.delete(us)
                self.ormdb.commit()

                ret = { 'deleted ID': us.cid }
            else:
                ret_code = HTTP_NOT_FOUND
                ret = { 'error': 'cant delete user object for given pseudo' }

        except tornado.web.MissingArgumentError as e:
            ret_code = HTTP_BAD_REQUEST
            ret = { 'error': 'pseudo parameter must be provided' }

        self.respond(ret, ret_code)
