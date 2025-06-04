module default {
    type Student {
        required property tg_id -> int64;
        required property name -> str {
            constraint max_len_value(64);
        };
        property group_num -> str {
            constraint max_len_value(16);
        };
        
        multi link team_memberships := .<student[is TeamMember];
        multi link sprint_reports := .<student[is SprintReport];
        multi link ratings_given := .<assessor[is TeamMemberRating];
        multi link ratings_received := .<assessed[is TeamMemberRating];
        multi link teams_administered := .<admin[is Team];
        
        constraint exclusive on (.tg_id);
    }
    
    type Team {
        required property team_name -> str {
            constraint max_len_value(64);
        };
        required property product_name -> str {
            constraint max_len_value(100);
        };
        required property invite_code -> str {
            constraint max_len_value(8);
        };
        required link admin -> Student;
        
        multi link members := .<team[is TeamMember];
        
        constraint exclusive on (.invite_code);
    }
    
    type TeamMember {
        required link team -> Team;
        required link student -> Student;
        required property role -> str {
            constraint max_len_value(32);
        };
        
        constraint exclusive on ((.team, .student));
    }
    
    type SprintReport {
        required link student -> Student;
        required property sprint_num -> int32;
        required property report_date -> datetime {
            default := datetime_current();
        };
        required property report_text -> str;
        
        constraint exclusive on ((.student, .sprint_num));
    }
    
    type TeamMemberRating {
        required link assessor -> Student;
        required link assessed -> Student;
        required property overall_rating -> int16 {
            constraint min_value(1);
            constraint max_value(10);
        };
        required property advantages -> str;
        required property disadvantages -> str;
        required property rate_date -> datetime {
            default := datetime_current();
        };
        
        constraint exclusive on ((.assessor, .assessed));
        constraint expression on (__subject__.assessor != __subject__.assessed);
    }
}