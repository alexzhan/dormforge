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
}
function isMail(mail) {
    var filter = /^([a-zA-Z0-9_\.\-])+\@(([a-zA-Z0-9\-])+\.)+([a-zA-Z0-9]{2,4})$/;
    if (filter.test(mail)) return true;
    else return false;
}
