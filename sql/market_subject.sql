INSERT INTO `market_subject` (`code`,`name`,`level`,`market_id`,`parent_id`,`trans_plus`,`dpl_rule`,`dt_opened`,`dt_created`,`dt_updated`)
VALUES
('XSHG-A','A股-SH',1,'XSHG',null,null,null,'1990-12-19','2020-11-04','2020-11-04'),
('XSHE-A','A股-SZ',1,'XSHE',null,null,null,'1990-11-01','2020-11-04','2020-11-04'),
('XSHG-A-MAIN','主板-SH',2,'XSHG','XSHG-A',1,
    '-1 if name[0:1] in ["N","C"] else 0.05 if name[0:2] == "ST" or name[0:3] == "*ST" else 0.1',
    '1990-12-19','2020-11-04','2020-11-04'),
('XSHG-A-STAR','科创板-SH',2,'XSHG','XSHG-A',1,
    '-1 if name[0:1] in ["N","C"] else 0.2',
    '2019-06-13','2020-11-04','2020-11-04'),
('XSHE-A-MAIN','主板-SZ',2,'XSHE','XSHE-A',1,
    '-1 if name[0:1] in ["N","C"] else 0.05 if name[0:2] == "ST" or name[0:3] == "*ST" else 0.1',
    '1990-12-01','2020-11-04','2020-11-04'),
('XSHE-A-SME','中小企业板-SZ',2,'XSHE','XSHE-A',1,
    '-1 if name[0:1] in ["N","C"] else 0.05 if name[0:2] == "ST" or name[0:3] == "*ST" else 0.1',
    '2004-06-25','2020-11-04','2020-11-04'),
('XSHE-A-CHINEXT','创业板-SZ',2,'XSHE','XSHE-A',1,
    '-1 if name[0:1] in ["N","C"] else 0.2',
    '2009-10-30','2020-11-04','2020-11-04');
