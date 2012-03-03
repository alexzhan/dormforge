function pubnote(notetype,pubtype) {
    if (pubtype == 1) {
        if ($("#secret").attr("checked")=="checked"){
            if (notetype == 0) notetype = 1;        
            else if (notetype == 1) notetype = 0;        
        }
    }
    var notetitle = $("#title").val();
    var notecontent = $("#content").val();
    var mark = 1;
    $("#notetitle").removeClass("error");
    $("#notecontent").removeClass("error");
    if(notetitle.length == 0){
        $("#notetitle").removeClass();
        $("#notetitle").addClass("control-group error");
        mark = 0;
    }
    if(notecontent.length == 0) {
        $("#notecontent").removeClass();
        $("#notecontent").addClass("control-group error");
        mark = 0;
    }
    if(!mark) return false;
    $.ajax({
        type:'POST',
        url:'/note/touch',
        data:{notetype:notetype,
            notetitle:notetitle,
            notecontent:notecontent,
            id:$("#noteid").val(),
            _xsrf:getCookie('_xsrf')},
        success:function(data){
            if(data == "right")
              window.location.href="/";
        }
    });
    return false;
}
function getCookie(name) {
    var r = document.cookie.match('\\b' + name + '=([^;]*)\\b');
    return r ? r[1] : undefined;
}
