CREATE MIGRATION m1daeydpj2lrn5hygc3jfaniygjn2v5ma5n5c2vzrrsihzx7mtwpbq
    ONTO initial
{
  CREATE TYPE default::Student {
      CREATE REQUIRED PROPERTY tg_id: std::int64;
      CREATE CONSTRAINT std::exclusive ON (.tg_id);
      CREATE PROPERTY group_num: std::str {
          CREATE CONSTRAINT std::max_len_value(16);
      };
      CREATE REQUIRED PROPERTY name: std::str {
          CREATE CONSTRAINT std::max_len_value(64);
      };
  };
  CREATE TYPE default::Team {
      CREATE REQUIRED LINK admin: default::Student;
      CREATE REQUIRED PROPERTY invite_code: std::str {
          CREATE CONSTRAINT std::max_len_value(8);
      };
      CREATE CONSTRAINT std::exclusive ON (.invite_code);
      CREATE REQUIRED PROPERTY product_name: std::str {
          CREATE CONSTRAINT std::max_len_value(100);
      };
      CREATE REQUIRED PROPERTY team_name: std::str {
          CREATE CONSTRAINT std::max_len_value(64);
      };
  };
  CREATE TYPE default::TeamMember {
      CREATE REQUIRED LINK student: default::Student;
      CREATE REQUIRED LINK team: default::Team;
      CREATE CONSTRAINT std::exclusive ON ((.team, .student));
      CREATE REQUIRED PROPERTY role: std::str {
          CREATE CONSTRAINT std::max_len_value(32);
      };
  };
  ALTER TYPE default::Student {
      CREATE MULTI LINK team_memberships := (.<student[IS default::TeamMember]);
  };
  ALTER TYPE default::Team {
      CREATE MULTI LINK members := (.<team[IS default::TeamMember]);
  };
  ALTER TYPE default::Student {
      CREATE MULTI LINK teams_administered := (.<admin[IS default::Team]);
  };
  CREATE TYPE default::SprintReport {
      CREATE REQUIRED LINK student: default::Student;
      CREATE REQUIRED PROPERTY sprint_num: std::int32;
      CREATE CONSTRAINT std::exclusive ON ((.student, .sprint_num));
      CREATE REQUIRED PROPERTY report_date: std::datetime {
          SET default := (std::datetime_current());
      };
      CREATE REQUIRED PROPERTY report_text: std::str;
  };
  ALTER TYPE default::Student {
      CREATE MULTI LINK sprint_reports := (.<student[IS default::SprintReport]);
  };
  CREATE TYPE default::TeamMemberRating {
      CREATE REQUIRED LINK assessed: default::Student;
      CREATE REQUIRED LINK assessor: default::Student;
      CREATE CONSTRAINT std::exclusive ON ((.assessor, .assessed));
      CREATE CONSTRAINT std::expression ON ((__subject__.assessor != __subject__.assessed));
      CREATE REQUIRED PROPERTY advantages: std::str;
      CREATE REQUIRED PROPERTY disadvantages: std::str;
      CREATE REQUIRED PROPERTY overall_rating: std::int16 {
          CREATE CONSTRAINT std::max_value(10);
          CREATE CONSTRAINT std::min_value(1);
      };
      CREATE REQUIRED PROPERTY rate_date: std::datetime {
          SET default := (std::datetime_current());
      };
  };
  ALTER TYPE default::Student {
      CREATE MULTI LINK ratings_given := (.<assessor[IS default::TeamMemberRating]);
      CREATE MULTI LINK ratings_received := (.<assessed[IS default::TeamMemberRating]);
  };
};