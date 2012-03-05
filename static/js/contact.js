function submitfunction(){
    var mark = 1;
    if($("#username").val().length == 0){
        $("#idcontrol-group").removeClass();
        $("#idcontrol-group").addClass("control-group error");
        $("#usernamehelp").html("请输入姓名");
        mark = 0;
    }
    if($("#username").val().length > 16){
        $("#idcontrol-group").removeClass();
        $("#idcontrol-group").addClass("control-group error");
        $("#usernamehelp").html("亲，您的姓名太长了吧:)");
        mark = 0;
    }
    if($("#email").val().length == 0) {
        $("#emailcontrol-group").removeClass();
        $("#emailcontrol-group").addClass("control-group error");
        $("#emailhelp").html("请输入邮箱");
        mark = 0;
    }
    if($("#email").val().length != 0 && !isMail($("#email").val())) {
        $("#emailcontrol-group").removeClass();
        $("#emailcontrol-group").addClass("control-group error");
        $("#emailhelp").html("邮箱不符合规则");
        mark = 0;
    }
    if($("#subject").val().length == 0) {
        $("#subjectcontrol-group").removeClass();
        $("#subjectcontrol-group").addClass("control-group error");
        $("#subjecthelp").html("请输入主题");
        mark = 0;
    }
    if($("#comment").val().length == 0) {
        $("#commentcontrol-group").removeClass();
        $("#commentcontrol-group").addClass("control-group error");
        $("#commenthelp").html("请输入内容");
        mark = 0;
    }
    if(!mark) return false;
    var username = $("#username").val();
    var email = $("#email").val();
    var subject = $("#subject").val();
    var comment = $("#comment").val();
    var alertstr = "<div class='alert alert-success'><a class='close' data-dismiss='alert' href='#'>×</a>您的反馈我们已收到，谢谢！</div>";
    $.ajax({
        type:'POST',
        url:'/contact',
        data:{username:username,email:email,subject:subject,comment:comment,_xsrf:getCookie('_xsrf')},
        success:function(data){
            if(data == "right"){
                $(alertstr).insertBefore(".container .content");
                $("#subject").val("");
                $("#comment").val("");
            }
        }       
    });
    return false;
}
