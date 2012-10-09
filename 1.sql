BEGIN;
CREATE TABLE "aidadb_computer" (
    "id" serial NOT NULL PRIMARY KEY,
    "uuid" uuid NOT NULL UNIQUE,
    "hostname" varchar(765) NOT NULL UNIQUE,
    "ip_address" varchar(90) NOT NULL UNIQUE,
    "scratch_location" varchar(765) NOT NULL,
    "description" text NOT NULL,
    "hdata" text NOT NULL,
    "jdata" text NOT NULL
)
;
CREATE TABLE "aidadb_codeattr" (
    "id" serial NOT NULL PRIMARY KEY,
    "uuid" uuid NOT NULL UNIQUE,
    "title" varchar(765) NOT NULL UNIQUE,
    "description" text NOT NULL,
    "datatype" varchar(18) NOT NULL,
    "isnumber" boolean NOT NULL,
    "hdata" text NOT NULL,
    "jdata" text NOT NULL
)
;
CREATE TABLE "aidadb_codegroup" (
    "id" serial NOT NULL PRIMARY KEY,
    "uuid" uuid NOT NULL UNIQUE,
    "title" varchar(765) NOT NULL UNIQUE,
    "description" text NOT NULL,
    "time_stamp" timestamp with time zone NOT NULL,
    "jdata" text NOT NULL,
    "hdata" text NOT NULL
)
;
CREATE TABLE "aidadb_codestatus" (
    "id" serial NOT NULL PRIMARY KEY,
    "uuid" uuid NOT NULL UNIQUE,
    "title" varchar(765) NOT NULL UNIQUE,
    "description" text NOT NULL
)
;
CREATE TABLE "aidadb_codetype" (
    "id" serial NOT NULL PRIMARY KEY,
    "uuid" uuid NOT NULL UNIQUE,
    "title" varchar(765) NOT NULL UNIQUE,
    "description" text NOT NULL
)
;
CREATE TABLE "aidadb_code_groups" (
    "id" serial NOT NULL PRIMARY KEY,
    "code_id" integer NOT NULL,
    "codegroup_id" integer NOT NULL REFERENCES "aidadb_codegroup" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("code_id", "codegroup_id")
)
;
CREATE TABLE "aidadb_code" (
    "id" serial NOT NULL PRIMARY KEY,
    "uuid" uuid NOT NULL UNIQUE,
    "title" varchar(765) NOT NULL UNIQUE,
    "type_id" integer NOT NULL REFERENCES "aidadb_codetype" ("id") DEFERRABLE INITIALLY DEFERRED,
    "computer_id" integer NOT NULL REFERENCES "aidadb_computer" ("id") DEFERRABLE INITIALLY DEFERRED,
    "status_id" integer NOT NULL REFERENCES "aidadb_codestatus" ("id") DEFERRABLE INITIALLY DEFERRED,
    "user_id" integer,
    "description" text NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    "hdata" text NOT NULL,
    "jdata" text NOT NULL
)
;
ALTER TABLE "aidadb_code_groups" ADD CONSTRAINT "code_id_refs_id_baf451f7" FOREIGN KEY ("code_id") REFERENCES "aidadb_code" ("id") DEFERRABLE INITIALLY DEFERRED;
CREATE TABLE "aidadb_codeattrval" (
    "id" serial NOT NULL PRIMARY KEY,
    "type" varchar(18) NOT NULL,
    "numval" double precision,
    "strval" text,
    "element_id" integer NOT NULL REFERENCES "aidadb_code" ("id") DEFERRABLE INITIALLY DEFERRED,
    "attr_id" integer NOT NULL REFERENCES "aidadb_codeattr" ("id") DEFERRABLE INITIALLY DEFERRED
)
;
CREATE TABLE "aidadb_elementattr" (
    "id" serial NOT NULL PRIMARY KEY,
    "uuid" uuid NOT NULL UNIQUE,
    "title" varchar(765) NOT NULL UNIQUE,
    "description" text NOT NULL,
    "datatype" varchar(18) NOT NULL,
    "isnumber" boolean NOT NULL,
    "hdata" text NOT NULL,
    "jdata" text NOT NULL
)
;
CREATE TABLE "aidadb_elementgroup" (
    "id" serial NOT NULL PRIMARY KEY,
    "uuid" uuid NOT NULL UNIQUE,
    "title" varchar(765) NOT NULL UNIQUE,
    "description" text NOT NULL,
    "time_stamp" timestamp with time zone NOT NULL,
    "jdata" text NOT NULL,
    "hdata" text NOT NULL
)
;
CREATE TABLE "aidadb_element_groups" (
    "id" serial NOT NULL PRIMARY KEY,
    "element_id" integer NOT NULL,
    "elementgroup_id" integer NOT NULL REFERENCES "aidadb_elementgroup" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("element_id", "elementgroup_id")
)
;
CREATE TABLE "aidadb_element" (
    "id" serial NOT NULL PRIMARY KEY,
    "name" varchar(135) NOT NULL UNIQUE,
    "symbol" varchar(21) NOT NULL UNIQUE,
    "mass" double precision NOT NULL,
    "hdata" text NOT NULL,
    "jdata" text NOT NULL
)
;
ALTER TABLE "aidadb_element_groups" ADD CONSTRAINT "element_id_refs_id_de3dadab" FOREIGN KEY ("element_id") REFERENCES "aidadb_element" ("id") DEFERRABLE INITIALLY DEFERRED;
CREATE TABLE "aidadb_elementattrval" (
    "id" serial NOT NULL PRIMARY KEY,
    "type" varchar(18) NOT NULL,
    "numval" double precision,
    "strval" text,
    "element_id" integer NOT NULL REFERENCES "aidadb_element" ("id") DEFERRABLE INITIALLY DEFERRED,
    "attr_id" integer NOT NULL REFERENCES "aidadb_elementattr" ("id") DEFERRABLE INITIALLY DEFERRED
)
;
CREATE TABLE "aidadb_potbasisattr" (
    "id" serial NOT NULL PRIMARY KEY,
    "uuid" uuid NOT NULL UNIQUE,
    "title" varchar(765) NOT NULL UNIQUE,
    "description" text NOT NULL,
    "datatype" varchar(18) NOT NULL,
    "isnumber" boolean NOT NULL,
    "hdata" text NOT NULL,
    "jdata" text NOT NULL
)
;
CREATE TABLE "aidadb_potbasisgroup" (
    "id" serial NOT NULL PRIMARY KEY,
    "uuid" uuid NOT NULL UNIQUE,
    "title" varchar(765) NOT NULL UNIQUE,
    "description" text NOT NULL,
    "time_stamp" timestamp with time zone NOT NULL,
    "jdata" text NOT NULL,
    "hdata" text NOT NULL
)
;
CREATE TABLE "aidadb_potbasisstatus" (
    "id" serial NOT NULL PRIMARY KEY,
    "uuid" uuid NOT NULL UNIQUE,
    "title" varchar(765) NOT NULL UNIQUE,
    "description" text NOT NULL
)
;
CREATE TABLE "aidadb_potbasistype" (
    "id" serial NOT NULL PRIMARY KEY,
    "uuid" uuid NOT NULL UNIQUE,
    "title" varchar(765) NOT NULL UNIQUE,
    "description" text NOT NULL
)
;
CREATE TABLE "aidadb_potbasis_element" (
    "id" serial NOT NULL PRIMARY KEY,
    "potbasis_id" integer NOT NULL,
    "element_id" integer NOT NULL REFERENCES "aidadb_element" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("potbasis_id", "element_id")
)
;
CREATE TABLE "aidadb_potbasis_groups" (
    "id" serial NOT NULL PRIMARY KEY,
    "potbasis_id" integer NOT NULL,
    "potbasisgroup_id" integer NOT NULL REFERENCES "aidadb_potbasisgroup" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("potbasis_id", "potbasisgroup_id")
)
;
CREATE TABLE "aidadb_potbasis" (
    "id" serial NOT NULL PRIMARY KEY,
    "uuid" uuid NOT NULL UNIQUE,
    "title" varchar(765) NOT NULL UNIQUE,
    "type_id" integer NOT NULL REFERENCES "aidadb_potbasistype" ("id") DEFERRABLE INITIALLY DEFERRED,
    "status_id" integer NOT NULL REFERENCES "aidadb_potbasisstatus" ("id") DEFERRABLE INITIALLY DEFERRED,
    "user_id" integer NOT NULL,
    "time_stamp" timestamp with time zone NOT NULL,
    "description" text NOT NULL,
    "hdata" text NOT NULL,
    "jdata" text NOT NULL
)
;
ALTER TABLE "aidadb_potbasis_element" ADD CONSTRAINT "potbasis_id_refs_id_50d8644e" FOREIGN KEY ("potbasis_id") REFERENCES "aidadb_potbasis" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "aidadb_potbasis_groups" ADD CONSTRAINT "potbasis_id_refs_id_4716651b" FOREIGN KEY ("potbasis_id") REFERENCES "aidadb_potbasis" ("id") DEFERRABLE INITIALLY DEFERRED;
CREATE TABLE "aidadb_potbasisattrval" (
    "id" serial NOT NULL PRIMARY KEY,
    "type" varchar(18) NOT NULL,
    "numval" double precision,
    "strval" text,
    "potbasis_id" integer NOT NULL REFERENCES "aidadb_potbasis" ("id") DEFERRABLE INITIALLY DEFERRED,
    "attr_id" integer NOT NULL REFERENCES "aidadb_potbasisattr" ("id") DEFERRABLE INITIALLY DEFERRED
)
;
CREATE TABLE "aidadb_project" (
    "id" serial NOT NULL PRIMARY KEY,
    "uuid" uuid NOT NULL UNIQUE,
    "title" varchar(765) NOT NULL UNIQUE,
    "description" text NOT NULL
)
;
CREATE TABLE "aidadb_strucattr" (
    "id" serial NOT NULL PRIMARY KEY,
    "uuid" uuid NOT NULL UNIQUE,
    "title" varchar(765) NOT NULL UNIQUE,
    "description" text NOT NULL,
    "datatype" varchar(18) NOT NULL,
    "isnumber" boolean NOT NULL,
    "hdata" text NOT NULL,
    "jdata" text NOT NULL
)
;
CREATE TABLE "aidadb_strucgroup" (
    "id" serial NOT NULL PRIMARY KEY,
    "uuid" uuid NOT NULL UNIQUE,
    "title" varchar(765) NOT NULL UNIQUE,
    "description" text NOT NULL,
    "time_stamp" timestamp with time zone NOT NULL,
    "jdata" text NOT NULL,
    "hdata" text NOT NULL
)
;
CREATE TABLE "aidadb_strucstatus" (
    "id" serial NOT NULL PRIMARY KEY,
    "uuid" uuid NOT NULL UNIQUE,
    "title" varchar(765) NOT NULL UNIQUE,
    "description" text NOT NULL
)
;
CREATE TABLE "aidadb_structype" (
    "id" serial NOT NULL PRIMARY KEY,
    "uuid" uuid NOT NULL UNIQUE,
    "title" varchar(765) NOT NULL UNIQUE,
    "description" text NOT NULL
)
;
CREATE TABLE "aidadb_struc_parent" (
    "id" serial NOT NULL PRIMARY KEY,
    "from_struc_id" integer NOT NULL,
    "to_struc_id" integer NOT NULL,
    UNIQUE ("from_struc_id", "to_struc_id")
)
;
CREATE TABLE "aidadb_struc_groups" (
    "id" serial NOT NULL PRIMARY KEY,
    "struc_id" integer NOT NULL,
    "strucgroup_id" integer NOT NULL REFERENCES "aidadb_strucgroup" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("struc_id", "strucgroup_id")
)
;
CREATE TABLE "aidadb_struc" (
    "id" serial NOT NULL PRIMARY KEY,
    "uuid" uuid NOT NULL UNIQUE,
    "formula" varchar(765) NOT NULL,
    "user_id" integer NOT NULL,
    "type_id" integer NOT NULL REFERENCES "aidadb_structype" ("id") DEFERRABLE INITIALLY DEFERRED,
    "description" text NOT NULL,
    "time_stamp" timestamp with time zone NOT NULL,
    "hdata" text NOT NULL,
    "jdata" text NOT NULL
)
;
ALTER TABLE "aidadb_struc_parent" ADD CONSTRAINT "from_struc_id_refs_id_d6b7a175" FOREIGN KEY ("from_struc_id") REFERENCES "aidadb_struc" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "aidadb_struc_parent" ADD CONSTRAINT "to_struc_id_refs_id_d6b7a175" FOREIGN KEY ("to_struc_id") REFERENCES "aidadb_struc" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "aidadb_struc_groups" ADD CONSTRAINT "struc_id_refs_id_c91148b" FOREIGN KEY ("struc_id") REFERENCES "aidadb_struc" ("id") DEFERRABLE INITIALLY DEFERRED;
CREATE TABLE "aidadb_strucattrval" (
    "id" serial NOT NULL PRIMARY KEY,
    "type" varchar(18) NOT NULL,
    "numval" double precision,
    "strval" text,
    "struc_id" integer NOT NULL REFERENCES "aidadb_struc" ("id") DEFERRABLE INITIALLY DEFERRED,
    "attr_id" integer NOT NULL REFERENCES "aidadb_strucattr" ("id") DEFERRABLE INITIALLY DEFERRED
)
;
CREATE TABLE "aidadb_composition" (
    "id" serial NOT NULL PRIMARY KEY,
    "struc_id" integer NOT NULL REFERENCES "aidadb_struc" ("id") DEFERRABLE INITIALLY DEFERRED,
    "element_id" integer NOT NULL REFERENCES "aidadb_element" ("id") DEFERRABLE INITIALLY DEFERRED,
    "quantity" integer NOT NULL
)
;
CREATE TABLE "aidadb_calcgroup" (
    "id" serial NOT NULL PRIMARY KEY,
    "uuid" uuid NOT NULL UNIQUE,
    "title" varchar(765) NOT NULL UNIQUE,
    "description" text NOT NULL,
    "time_stamp" timestamp with time zone NOT NULL,
    "jdata" text NOT NULL,
    "hdata" text NOT NULL
)
;
CREATE TABLE "aidadb_calcattr" (
    "id" serial NOT NULL PRIMARY KEY,
    "uuid" uuid NOT NULL UNIQUE,
    "title" varchar(765) NOT NULL UNIQUE,
    "description" text NOT NULL,
    "datatype" varchar(18) NOT NULL,
    "isnumber" boolean NOT NULL,
    "hdata" text NOT NULL,
    "jdata" text NOT NULL
)
;
CREATE TABLE "aidadb_calcstatus" (
    "id" serial NOT NULL PRIMARY KEY,
    "uuid" uuid NOT NULL UNIQUE,
    "title" varchar(765) NOT NULL UNIQUE,
    "description" text NOT NULL
)
;
CREATE TABLE "aidadb_calctype" (
    "id" serial NOT NULL PRIMARY KEY,
    "uuid" uuid NOT NULL UNIQUE,
    "title" varchar(765) NOT NULL UNIQUE,
    "description" text NOT NULL
)
;
CREATE TABLE "aidadb_calc_in_struc" (
    "id" serial NOT NULL PRIMARY KEY,
    "calc_id" integer NOT NULL,
    "struc_id" integer NOT NULL REFERENCES "aidadb_struc" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("calc_id", "struc_id")
)
;
CREATE TABLE "aidadb_calc_potbasis" (
    "id" serial NOT NULL PRIMARY KEY,
    "calc_id" integer NOT NULL,
    "potbasis_id" integer NOT NULL REFERENCES "aidadb_potbasis" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("calc_id", "potbasis_id")
)
;
CREATE TABLE "aidadb_calc_out_struc" (
    "id" serial NOT NULL PRIMARY KEY,
    "calc_id" integer NOT NULL,
    "struc_id" integer NOT NULL REFERENCES "aidadb_struc" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("calc_id", "struc_id")
)
;
CREATE TABLE "aidadb_calc_parent" (
    "id" serial NOT NULL PRIMARY KEY,
    "from_calc_id" integer NOT NULL,
    "to_calc_id" integer NOT NULL,
    UNIQUE ("from_calc_id", "to_calc_id")
)
;
CREATE TABLE "aidadb_calc_groups" (
    "id" serial NOT NULL PRIMARY KEY,
    "calc_id" integer NOT NULL,
    "calcgroup_id" integer NOT NULL REFERENCES "aidadb_calcgroup" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("calc_id", "calcgroup_id")
)
;
CREATE TABLE "aidadb_calc" (
    "id" serial NOT NULL PRIMARY KEY,
    "uuid" uuid NOT NULL UNIQUE,
    "code_id" integer NOT NULL REFERENCES "aidadb_code" ("id") DEFERRABLE INITIALLY DEFERRED,
    "project_id" integer NOT NULL REFERENCES "aidadb_project" ("id") DEFERRABLE INITIALLY DEFERRED,
    "status_id" integer NOT NULL REFERENCES "aidadb_calcstatus" ("id") DEFERRABLE INITIALLY DEFERRED,
    "type_id" integer NOT NULL REFERENCES "aidadb_calctype" ("id") DEFERRABLE INITIALLY DEFERRED,
    "user_id" integer NOT NULL,
    "computer_id" integer NOT NULL REFERENCES "aidadb_computer" ("id") DEFERRABLE INITIALLY DEFERRED,
    "qjob" integer NOT NULL,
    "description" text NOT NULL,
    "time_stamp" timestamp with time zone NOT NULL,
    "hdata" text NOT NULL,
    "jdata" text NOT NULL
)
;
ALTER TABLE "aidadb_calc_in_struc" ADD CONSTRAINT "calc_id_refs_id_93318140" FOREIGN KEY ("calc_id") REFERENCES "aidadb_calc" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "aidadb_calc_potbasis" ADD CONSTRAINT "calc_id_refs_id_13fcb380" FOREIGN KEY ("calc_id") REFERENCES "aidadb_calc" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "aidadb_calc_out_struc" ADD CONSTRAINT "calc_id_refs_id_34d328e0" FOREIGN KEY ("calc_id") REFERENCES "aidadb_calc" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "aidadb_calc_parent" ADD CONSTRAINT "from_calc_id_refs_id_6e738161" FOREIGN KEY ("from_calc_id") REFERENCES "aidadb_calc" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "aidadb_calc_parent" ADD CONSTRAINT "to_calc_id_refs_id_6e738161" FOREIGN KEY ("to_calc_id") REFERENCES "aidadb_calc" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "aidadb_calc_groups" ADD CONSTRAINT "calc_id_refs_id_2bdfa779" FOREIGN KEY ("calc_id") REFERENCES "aidadb_calc" ("id") DEFERRABLE INITIALLY DEFERRED;
CREATE TABLE "aidadb_calcattrval" (
    "id" serial NOT NULL PRIMARY KEY,
    "type" varchar(18) NOT NULL,
    "numval" double precision,
    "strval" text,
    "calc_id" integer NOT NULL REFERENCES "aidadb_calc" ("id") DEFERRABLE INITIALLY DEFERRED,
    "attr_id" integer NOT NULL REFERENCES "aidadb_calcattr" ("id") DEFERRABLE INITIALLY DEFERRED
)
;
-- The following references should be added but depend on non-existent tables:
-- ALTER TABLE "aidadb_code" ADD CONSTRAINT "user_id_refs_id_cbe68750" FOREIGN KEY ("user_id") REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED;
-- ALTER TABLE "aidadb_potbasis" ADD CONSTRAINT "user_id_refs_id_3087f446" FOREIGN KEY ("user_id") REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED;
-- ALTER TABLE "aidadb_struc" ADD CONSTRAINT "user_id_refs_id_62eafc7f" FOREIGN KEY ("user_id") REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED;
-- ALTER TABLE "aidadb_calc" ADD CONSTRAINT "user_id_refs_id_e65402e8" FOREIGN KEY ("user_id") REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED;
CREATE INDEX "aidadb_code_type_id" ON "aidadb_code" ("type_id");
CREATE INDEX "aidadb_code_computer_id" ON "aidadb_code" ("computer_id");
CREATE INDEX "aidadb_code_status_id" ON "aidadb_code" ("status_id");
CREATE INDEX "aidadb_code_user_id" ON "aidadb_code" ("user_id");
CREATE INDEX "aidadb_codeattrval_element_id" ON "aidadb_codeattrval" ("element_id");
CREATE INDEX "aidadb_codeattrval_attr_id" ON "aidadb_codeattrval" ("attr_id");
CREATE INDEX "aidadb_elementattrval_element_id" ON "aidadb_elementattrval" ("element_id");
CREATE INDEX "aidadb_elementattrval_attr_id" ON "aidadb_elementattrval" ("attr_id");
CREATE INDEX "aidadb_potbasis_type_id" ON "aidadb_potbasis" ("type_id");
CREATE INDEX "aidadb_potbasis_status_id" ON "aidadb_potbasis" ("status_id");
CREATE INDEX "aidadb_potbasis_user_id" ON "aidadb_potbasis" ("user_id");
CREATE INDEX "aidadb_potbasisattrval_potbasis_id" ON "aidadb_potbasisattrval" ("potbasis_id");
CREATE INDEX "aidadb_potbasisattrval_attr_id" ON "aidadb_potbasisattrval" ("attr_id");
CREATE INDEX "aidadb_struc_user_id" ON "aidadb_struc" ("user_id");
CREATE INDEX "aidadb_struc_type_id" ON "aidadb_struc" ("type_id");
CREATE INDEX "aidadb_strucattrval_struc_id" ON "aidadb_strucattrval" ("struc_id");
CREATE INDEX "aidadb_strucattrval_attr_id" ON "aidadb_strucattrval" ("attr_id");
CREATE INDEX "aidadb_composition_struc_id" ON "aidadb_composition" ("struc_id");
CREATE INDEX "aidadb_composition_element_id" ON "aidadb_composition" ("element_id");
CREATE INDEX "aidadb_calc_code_id" ON "aidadb_calc" ("code_id");
CREATE INDEX "aidadb_calc_project_id" ON "aidadb_calc" ("project_id");
CREATE INDEX "aidadb_calc_status_id" ON "aidadb_calc" ("status_id");
CREATE INDEX "aidadb_calc_type_id" ON "aidadb_calc" ("type_id");
CREATE INDEX "aidadb_calc_user_id" ON "aidadb_calc" ("user_id");
CREATE INDEX "aidadb_calc_computer_id" ON "aidadb_calc" ("computer_id");
CREATE INDEX "aidadb_calcattrval_calc_id" ON "aidadb_calcattrval" ("calc_id");
CREATE INDEX "aidadb_calcattrval_attr_id" ON "aidadb_calcattrval" ("attr_id");
COMMIT;
