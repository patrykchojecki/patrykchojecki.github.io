/* eslint-disable */
/*
 * FitVids 1.1
 *
 * Copyright 2013, Chris Coyier - https://css-tricks.com + Dave Rupert - https://daverupert.com
 * Released under the WTFPL license - https://sam.zoy.org/wtfpl/
 */
(function ($) {
  'use strict';

  $.fn.fitVids = function (options) {
    var settings = {
      customSelector: null,
      ignore: null
    };

    if (!document.getElementById('fit-vids-style')) {
      var head = document.head || document.getElementsByTagName('head')[0];
      var css = '.fluid-width-video-wrapper{width:100%;position:relative;padding:0;}' +
        '.fluid-width-video-wrapper iframe,.fluid-width-video-wrapper object,.fluid-width-video-wrapper embed {' +
        'position:absolute;top:0;left:0;width:100%;height:100%;}';
      var div = document.createElement('div');
      div.innerHTML = '<p>x</p><style id="fit-vids-style">' + css + '</style>';
      head.appendChild(div.childNodes[1]);
    }

    if (options) {
      $.extend(settings, options);
    }

    return this.each(function () {
      var selectors = [
        'iframe[src*="player.vimeo.com"]',
        'iframe[src*="youtube.com"]',
        'iframe[src*="youtube-nocookie.com"]',
        'iframe[src*="kickstarter.com"][src*="video.html"]',
        'object',
        'embed'
      ];

      if (settings.customSelector) {
        selectors.push(settings.customSelector);
      }

      var ignoreList = '.fitvidsignore';
      if (settings.ignore) {
        ignoreList = ignoreList + ', ' + settings.ignore;
      }

      var videos = $(this).find(selectors.join(','));
      videos = videos.not('object object');
      videos = videos.not(ignoreList);

      videos.each(function (index) {
        var $video = $(this);
        if ($video.parents(ignoreList).length > 0 ||
            (this.tagName.toLowerCase() === 'embed' && $video.parent('object').length) ||
            $video.parent('.fluid-width-video-wrapper').length) {
          return;
        }

        if (!$video.css('height') && !$video.css('width') &&
            (isNaN($video.attr('height')) || isNaN($video.attr('width')))) {
          $video.attr('height', 9);
          $video.attr('width', 16);
        }

        var height = this.tagName.toLowerCase() === 'object' ||
          ($video.attr('height') && !isNaN(parseInt($video.attr('height'), 10)))
          ? parseInt($video.attr('height'), 10)
          : $video.height();
        var width = isNaN(parseInt($video.attr('width'), 10))
          ? $video.width()
          : parseInt($video.attr('width'), 10);
        var aspectRatio = height / width;

        if (!$video.attr('id')) {
          $video.attr('id', 'fitvid' + index);
        }

        $video
          .wrap('<div class="fluid-width-video-wrapper"></div>')
          .parent('.fluid-width-video-wrapper')
          .css('padding-top', (aspectRatio * 100) + '%');

        $video.removeAttr('height').removeAttr('width');
      });
    });
  };
}(window.jQuery || window.Zepto));
