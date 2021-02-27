/**
 * Created by ivanjr on 11/06/15.
 */

//
//$(function(){
//
//    var caminho = $('#caminho'),
//        pos = caminho.offset();
//
//        $(window).scroll(function(){
//            if($(this).scrollTop() > pos.top && caminho.hasClass('default')){
//                caminho.fadeOut(0, function(){
//                    $(this).removeClass('default').addClass('fixed').fadeIn(0);
//                });
//            } else if($(this).scrollTop() <= pos.top && caminho.hasClass('fixed')){
//                caminho.fadeOut(0, function(){
//                    $(this).removeClass('fixed').addClass('default').fadeIn(0);
//                });
//            }
//        });
//
//});



function initAll(context) {
    if (!context) var context = "body";

    /* Action Bar */
    jQuery(context).find(".action-bar .has-child > a").click(function() {
        jQuery(this).next("ul").toggle();
        return false;
    });
    jQuery(context).find(".action-bar .has-child ul").hover(function() {
	}, function () {
		jQuery(this).hide("fast");
	});

	// Label Required
	jQuery(context).find("label.required, .required label").attr("title", "Preenchimento obrigatório");

	/* Action Links */
    jQuery(context).find(".action-print a").click(function() {
	    print();
        return false;
    });
    jQuery(context).find("#topodapagina").click(function(){
		jQuery('html, body').animate({scrollTop:0}, 'slow');
	});

	/* Âncoras */
	jQuery(context).find(".ancoras").click(function() {
		jQuery(this).toggleClass("hideInfo");
		jQuery(context).find(".com_ancora").toggleClass("hideInfo");
	});

    jQuery(context).find(".confirm, .danger, .icon-trash").not(".no-confirm, .ajax").click(function(e) {
        var result = confirm(jQuery(this).attr("data-confirm") || "Tem certeza que deseja continuar?");

        if(result != true) {
            e.preventDefault();
        }
    });

    jQuery(context).find(".voltar").click(function() {
        window.history.back();
    });

	jQuery(context).find("#menu-device a").click(function() {
        jQuery(context).find('nav > ul').toggle();
    });

    // Expandir
	jQuery(context).find(".action-bar .normalscreen").hide();
	jQuery(context).find(".action-bar .fullscreen").click(function() {
		jQuery(this).hide();
		jQuery(context).find("aside, footer, h2").hide();
		jQuery(context).find(".action-bar .normalscreen").show();
		jQuery(context).find("article").addClass("fullscreen");
	});
	jQuery(context).find(".action-bar .normalscreen").click(function() {
		jQuery(this).hide();
		jQuery(context).find("aside, footer, h2").show();
		jQuery(context).find(".action-bar .fullscreen").show();
		jQuery(context).find("article").removeClass("fullscreen");
	});

    // esconder Links Sem Filhos
    jQuery(context).find(".action-bar .has-child").find("ul").each(function() {
        if (!jQuery(this).has("li").length) {
            jQuery(this).parent().hide();
        }
    });

}
jQuery(document).ready(function() {
    initAll();
    initMenu();

    /* Menu principal: Para dispositivos moveis */
    if (/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
        jQuery("body").addClass("hideSidebar");
    }
});