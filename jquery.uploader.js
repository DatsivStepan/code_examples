;(function($) {

    var defaults = {
        main_form:'panel_form',
        hided_input_field : 'hided_field',
        choose_button :'choose_button',
        archive_upload_button: 'BigArchiveImageFile',
        parsed_images_form_upload_action: '/panel/parsed_images/',
        actionFields: "actionFields"
    };

    $.fn.file_uploader = function(options) {

        var config = $.extend({}, defaults, options);

        // hide file input fields
        $("." + config.hided_input_field).hide();

        // fire sending of image archive file
        $("#" + config.archive_upload_button).change(function(evt) {
           //console.log(evt.target.files[0].size);
            var form = $(evt.target).parent("form");
            sendBigFile(form);
        });

        // bind button click and trigger click on file input
        $("." + config.choose_button).bind("click", function(evt){

            var hiden_field_id = $(evt.target).attr("class").split(" ")[1].trim();

            if (hiden_field_id != "submit") {
                $("#" + hiden_field_id).click();
            }
            if (hiden_field_id == "submit") {
                var upload_frame = iframeInit("file_uploader");
                $('.' + config.main_form).attr('target','file_uploader');
                $("." + config.main_form).submit();
                $(upload_frame).unbind();
                $(upload_frame).bind("onload", function(evt) {
                    callback(upload_frame);
                });
                $("." + config.main_form).find("input[type=text]").each(function(i, el) {  $("form")[i].reset(); });
            }
        });

        function reinit(frame) {
           $(frame).remove();
//            $("#result_div").fadeIn(300).delay(3000).fadeOut(400);
        }

        $("body").bind("remove_iframe", function(evt, target_frame) { reinit(target_frame); });

        function callback(frame) {
            $(frame).bind("load", function(evt) {
                var parent = window.parent;
//                var target_frame = $(evt.target);
//                result_div = document.createElement("div");
//                $(result_div).css("border","1px solid green").css("background-color","#5FED1D");
//                $(result_div).attr("id","result_div");
//                $(result_div).css("width","40em");
//                $(result_div).css("min-height", "2em");
//                $(result_div).css("z-index", "99");
//                $(result_div).css("position", "absolute");
//                $(result_div).text("Data was submited");
//                $(parent.document.body).prepend(result_div);
                $(parent.document.body).trigger("remove_iframe", [frame]);
            })
        }
        //Creates new form, append images archive input to new form, submits new form
        function sendBigFile(main_form) {
            var upload_frame = iframeInit("big_file_upload");

            var forms = $("body").find("form[name=big_file_upload]");
            if(forms.size()>0){ forms.remove(); }
            $("body").append("<form name='big_file_upload'></form>");
            var form = $("body").find("form[name=big_file_upload]");

            //console.log(form);
            form.attr("enctype","multipart/form-data");
            form.attr("target", upload_frame.attr("name"));
            form.attr("action", config.parsed_images_form_upload_action);
            form.attr("method", "post");
            //console.log(main_form.find("#" + config.archive_upload_button))
            form.prepend(main_form.find("#" + config.archive_upload_button));
            form.append(main_form.find("." + config.actionFields).clone().hide());
            var selected_opt = $($("select." + config.actionFields).get(0).options).filter(":selected").val();
            $($("select." + config.actionFields).get(1).options).each( function(i, option) {
                if ($(option).val() == selected_opt) {
                    $(option).attr("selected","selected");
                }
            });

            main_form.find("#" + config.archive_upload_button).remove();
            form.submit();
            //form.remove();
            $("#BigArchiveImageFile_Button").attr("disabled", "disabled");
            callback(upload_frame);
        }


        function iframeInit(frameName) {
            if ($("iframe[name=" + frameName + "]").size() == 0) {
                $("body").append("<iframe name='" + frameName + "'></iframe>");
            }
            var upload_frame = $("iframe[name=" + frameName + "]");
            $(upload_frame).css("width",0);
            $(upload_frame).css('height',0);
            $(upload_frame).css('border',0);

            return upload_frame
        }
        }



    }
    (jQuery))
