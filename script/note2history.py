from mysql2redis_commnum import db

notes = db.query("select * from fd_Note")
for note in notes:
    user = db.get("select name,domain from fd_People where id = %s", note.user_id)
    db.execute("insert into fd_NoteHistory(note_id,title,note,rev_num,rev_user_id,rev_user_name,rev_user_domain,revdate) values (%s,%s,%s,%s,%s,%s,%s,%s)", note.id,note.title,note.note,1,note.user_id,user.name,user.domain,note.pubdate)
