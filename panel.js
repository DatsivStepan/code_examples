if(!self.aromartClasses)
    self.aromartClasses = {};


self.aromartClasses.Controller = function () {
    this.InitInstance = function(){
        this.InitElements();
}
    this.InitElements = function(){
        this.elements = {};

        for(var i in this.elementsMapping)
            this.elements[i] = jQuery(this.elementsMapping[i]);

            };

    this.InitInstance();
}

self.aromartClasses.Page = function() {
    var curThis = this;

    this.elementsMapping = {
        chosen:  ".variants",
        action_fields: ".actionFields"
    }

    self.aromartClasses.Controller.call(this);

    this.InitInstance = function(){

        this.InitEvents();
    }

    this.InitEvents = function() {
        jQuery(this.elements.action_fields).parent().hide();

        jQuery(this.elements.chosen).bind("click", function(evt) {
            var variant_id = jQuery(evt.target).attr("id");
            jQuery(curThis.elements.action_fields).parent().show()
//            for(var item in $(evt.target)) {
//                console.log(item);
//            }
            var actions = jQuery(curThis.elements.action_fields);
            actions.hide();
//            console.log(variant_id);
            $(actions.get(variant_id)).show();
        })
    }

    this.InitInstance();
}

