from mysql2redis_commnum import db

notes = db.query("select * from fd_Note")
for note in notes:
    user = db.get("select name from fd_People where id = %s", note.user_id).name
    db.execute("insert into fd_NoteHistory(note_id,title,note,rev_num,rev_user_id,rev_user_text,revdate) values (%s,%s,%s,%s,%s,%s,%s)", note.id,note.title,note.note,1,note.user_id,user,note.pubdate)
