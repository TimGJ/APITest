/*
** Generates the tables for the inventory PoC.
**
** A rack may contain multiple servers.
** A server will contain multiple NICs
** A nic may have multiple IP addresses associated with it.
**
** TGJ 16 May 2018
 */

-- We have to drop tables in reverse order due to the FK constraints

drop table if exists inventory.ips;
drop table if exists inventory.nics;
drop table if exists inventory.servers;
drop table if exists inventory.racks;

create table if not exists racks (
  id integer not null auto_increment primary key,
  name varchar(20),
  commentary varchar(40)
);


create table if not exists inventory.servers (
  id integer not null auto_increment primary key, -- This is different from the SID!
  servicetag varchar(10) not null unique,
  sid integer not null unique,
  sotckid integer not null unique,
  rack_id integer,
  position integer,
  foreign key (rack_id)
    references inventory.racks(id)
    on update cascade
    on delete cascade
);

create table if not exists inventory.nics (
  id integer not null auto_increment primary key,
  server_id integer,
  mac char(12),
  foreign key (server_id)
    references inventory.servers(id)
    on update cascade
    on delete cascade
);

create table if not exists inventory.ips (
  id integer not null auto_increment primary key,
  nic_id integer,
  ip integer unsigned,
  foreign key (nic_id)
    references inventory.nics(id)
    on update cascade
    on delete cascade
);
