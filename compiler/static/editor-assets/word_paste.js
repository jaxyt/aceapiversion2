/*!
 * froala_editor v3.2.0 (https://www.froala.com/wysiwyg-editor)
 * License https://froala.com/wysiwyg-editor/terms/
 * Copyright 2014-2020 Froala Labs
 */

(function (global, factory) {
  typeof exports === 'object' && typeof module !== 'undefined' ? factory(require('froala-editor')) :
  typeof define === 'function' && define.amd ? define(['froala-editor'], factory) :
  (factory(global.FroalaEditor));
}(this, (function (FE) { 'use strict';

  FE = FE && FE.hasOwnProperty('default') ? FE['default'] : FE;

  Object.assign(FE.DEFAULTS, {
    wordDeniedTags: [],
    wordDeniedAttrs: [],
    wordAllowedStyleProps: ['font-family', 'font-size', 'background', 'color', 'width', 'text-align', 'vertical-align', 'background-color', 'padding', 'margin', 'height', 'margin-top', 'margin-left', 'margin-right', 'margin-bottom', 'text-decoration', 'font-weight', 'font-style', 'text-indent', 'border', 'border-.*', 'line-height', 'list-style-type'],
    wordPasteModal: true,
    wordPasteKeepFormatting: true
  });

  FE.PLUGINS.wordPaste = function (editor) {
    var $ = editor.$;
    var $modal;
    var modal_id = 'word_paste';
    var clipboard_html;
    var _v_shapes_map = {};
    /*
     * Init Word Paste.
     */

    function _init() {
      editor.events.on('paste.wordPaste', function (html) {
        clipboard_html = html;

        if (editor.opts.wordPasteModal) {
          _showModal();
        } else {
          clean(editor.opts.wordPasteKeepFormatting);
        }

        return false;
      });
    }
    /*
     * Build html body.
     */


    function _buildModalBody() {
      // Begin body.
      var body = '<div class="fr-word-paste-modal" style="padding: 20px 20px 10px 20px;">';
      body += '<p style="text-align: left;">' + editor.language.translate('The pasted content is coming from a Microsoft Word document. Do you want to keep the format or clean it up?') + '</p>';
      body += '<div style="text-align: right; margin-top: 50px;"><button class="fr-remove-word fr-command">' + editor.language.translate('Clean') + '</button> <button class="fr-keep-word fr-command">' + editor.language.translate('Keep') + '</button></div>'; // End body.

      body += '</div>';
      return body;
    }
    /*
     * Show modal.
     */


    function _showModal() {
      if (!$modal) {
        var head = '<h4><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 74.95 73.23" style="height: 25px; vertical-align: text-bottom; margin-right: 5px; display: inline-block"><defs><style>.a{fill:#2a5699;}.b{fill:#fff;}</style></defs><path class="a" d="M615.15,827.22h5.09V834c9.11.05,18.21-.09,27.32.05a2.93,2.93,0,0,1,3.29,3.25c.14,16.77,0,33.56.09,50.33-.09,1.72.17,3.63-.83,5.15-1.24.89-2.85.78-4.3.84-8.52,0-17,0-25.56,0v6.81h-5.32c-13-2.37-26-4.54-38.94-6.81q0-29.8,0-59.59c13.05-2.28,26.11-4.5,39.17-6.83Z" transform="translate(-575.97 -827.22)"/><path class="b" d="M620.24,836.59h28.1v54.49h-28.1v-6.81h22.14v-3.41H620.24v-4.26h22.14V873.2H620.24v-4.26h22.14v-3.41H620.24v-4.26h22.14v-3.41H620.24v-4.26h22.14v-3.41H620.24V846h22.14v-3.41H620.24Zm-26.67,15c1.62-.09,3.24-.16,4.85-.25,1.13,5.75,2.29,11.49,3.52,17.21,1-5.91,2-11.8,3.06-17.7,1.7-.06,3.41-.15,5.1-.26-1.92,8.25-3.61,16.57-5.71,24.77-1.42.74-3.55,0-5.24.09-1.13-5.64-2.45-11.24-3.47-16.9-1,5.5-2.29,10.95-3.43,16.42q-2.45-.13-4.92-.3c-1.41-7.49-3.07-14.93-4.39-22.44l4.38-.18c.88,5.42,1.87,10.82,2.64,16.25,1.2-5.57,2.43-11.14,3.62-16.71Z" transform="translate(-575.97 -827.22)"/></svg> ' + editor.language.translate('Word Paste Detected') + '</h4>';

        var body = _buildModalBody();

        var modalHash = editor.modals.create(modal_id, head, body);
        var $body = modalHash.$body;
        $modal = modalHash.$modal;
        modalHash.$modal.addClass('fr-middle');
        editor.events.bindClick($body, 'button.fr-remove-word', function () {
          var inst = $modal.data('instance') || editor;
          inst.wordPaste.clean();
        });
        editor.events.bindClick($body, 'button.fr-keep-word', function () {
          var inst = $modal.data('instance') || editor;
          inst.wordPaste.clean(true);
        }); // Resize help modal on window resize.

        editor.events.$on($(editor.o_win), 'resize', function () {
          editor.modals.resize(modal_id);
        });
      } // Show modal.


      editor.modals.show(modal_id); // Modal may not fit window size.

      editor.modals.resize(modal_id);
    }
    /*
     * Hide modal.
     */


    function _hideModal() {
      editor.modals.hide(modal_id);
    }
    /*
     * Word paste cleanup.
     */


    function clean(keep_formatting) {
      var wordAllowedStylePropsBackup = editor.opts.wordAllowedStyleProps;

      if (!keep_formatting) {
        editor.opts.wordAllowedStyleProps = [];
      } // Firefox paste.


      if (clipboard_html.indexOf('<colgroup>') === 0) {
        clipboard_html = '<table>' + clipboard_html + '</table>';
      } // Replace spaces.


      clipboard_html = clipboard_html.replace(/<span[\n\r ]*style='mso-spacerun:yes'>([\r\n\u00a0 ]*)<\/span>/g, function (str, match) {
        var spaces = '';
        var i = 0;

        while (i++ < match.length) {
          spaces += '&nbsp;';
        }

        return spaces;
      });
      clipboard_html = _wordClean(clipboard_html, editor.paste.getRtfClipboard()); // Remove unwanted spaces.

      var div = editor.doc.createElement('DIV');
      div.innerHTML = clipboard_html;
      editor.html.cleanBlankSpaces(div);
      clipboard_html = div.innerHTML;
      clipboard_html = editor.paste.cleanEmptyTagsAndDivs(clipboard_html); // Remove invisible space.

      clipboard_html = clipboard_html.replace(/\u200b/g, '');

      _hideModal(); // Clean the processed clipboard_html.


      editor.paste.clean(clipboard_html, true, true);
      editor.opts.wordAllowedStyleProps = wordAllowedStylePropsBackup;
    }
    /**
     * Remove a node. IE conpatible.
     */


    function _removeNode(node) {
      var parent = node.parentNode;

      if (!parent) {
        return;
      }

      node.parentNode.removeChild(node);
    }
    /*
     * Depth-first search traversing of the DOM.
     */


    function _traverse(node, callback) {
      // Process node.
      if (!callback(node)) {
        return;
      } // Expand node. Take its first child.


      var child = node.firstChild; // While all childs are traversed.

      while (child) {
        // Store the current child.
        var current_child = child; // Store the previous child.

        var previous_child = child.previousSibling; // Take next child.

        child = child.nextSibling; // Expand the current child.

        _traverse(current_child, callback); // An unwrap was made. Need to calculate again the next child.


        if (!current_child.previousSibling && !current_child.nextSibling && !current_child.parentNode && child && previous_child !== child.previousSibling && child.parentNode) {
          if (previous_child) {
            child = previous_child.nextSibling;
          } else {
            child = node.firstChild;
          }
        } // A list was created. Need to calculate again the next child.
        else if (!current_child.previousSibling && !current_child.nextSibling && !current_child.parentNode && child && !child.previousSibling && !child.nextSibling && !child.parentNode) {
            if (previous_child) {
              if (previous_child.nextSibling) {
                child = previous_child.nextSibling.nextSibling;
              } else {
                child = null;
              }
            } else {
              if (node.firstChild) {
                child = node.firstChild.nextSibling;
              }
            }
          }
      }
    }
    /*
     * Check if a node is a list. TODO: use Regex.
     */


    function _isList(node) {
      // Check if it has mso-list:l in its style attribute.
      if (!(node.getAttribute('style') && /mso-list:[\s]*l/gi.test(node.getAttribute('style').replace(/\n/gi, '')))) {
        return false;
      } // Using try-catch to skip undefined checking.


      try {
        // Check mso-list.
        if (!node.querySelector('[style="mso-list:Ignore"]')) {
          if (node.outerHTML && node.outerHTML.indexOf('<!--[if !supportLists]-->') >= 0) {
            return true;
          }

          return false;
        }
      } catch (e) {
        return false;
      }

      return true;
    }
    /*
     * Get list level based on level attribute from node style.
     */


    function _getListLevel(node) {
      return node.getAttribute('style').replace(/\n/gi, '').replace(/.*level([0-9]+?).*/gi, '$1');
    }
    /*
     * Get list content.
     */


    function _getListContent(node, head_style_hash) {
      var cloned_node = node.cloneNode(true); // Some lists might be wrapped in a link. So we need to unwrap.
      // if (cloned_node.firstElementChild && cloned_node.firstElementChild.tagName === 'A') {
      //   cloned_node = cloned_node.firstElementChild
      // }
      // Heading list.

      if (['H1', 'H2', 'H3', 'H4', 'H5', 'H6'].indexOf(node.tagName) !== -1) {
        var heading = document.createElement(node.tagName.toLowerCase());
        heading.setAttribute('style', node.getAttribute('style'));
        heading.innerHTML = cloned_node.innerHTML;
        cloned_node.innerHTML = heading.outerHTML;
      } // Clean node recursively.


      _traverse(cloned_node, function (node) {
        if (node.nodeType == Node.COMMENT_NODE && (editor.browser.msie || editor.browser.safari || editor.browser.edge)) {
          try {
            if (node.data === '[if !supportLists]') {
              node = node.nextSibling;

              while (node && node.nodeType !== Node.COMMENT_NODE) {
                var tmp = node.nextSibling;
                node.parentNode.removeChild(node);
                node = tmp;
              }

              if (node && node.nodeType == Node.COMMENT_NODE) {
                node.parentNode.removeChild(node);
              }
            }
          } catch (ex) {}
        }

        if (node.nodeType === Node.ELEMENT_NODE) {
          // Skip the first child which is an mso-list:Ignore node.
          // 1854 For handling extra characters 
          if (node.getAttribute('style') === 'mso-list:\nIgnore') node.setAttribute("style", "mso-list:Ignore");

          if (node.getAttribute('style') === 'mso-list:Ignore') {
            node.parentNode.removeChild(node);
          }

          node.setAttribute('style', _getAllowedListStyles(node));

          _cleanElement(node, head_style_hash);
        }

        return true;
      }); // Take content.


      var content = cloned_node.innerHTML; // Replace comments.

      content = content.replace(/<!--[\s\S]*?-->/gi, '');
      return content;
    }
    /*
     * Build ol/ul list.
     */


    function _buildList(node, head_style_hash, level, prev_margin) {
      // Check ol/ul.
      var order_regex = /[0-9a-zA-Z]./gi;
      var is_ordered = false;
      var prev_order;
      var previous_element_sibling;
      var browser = navigator.userAgent.toLowerCase();

      if (browser.indexOf('safari') != -1) {
        if (browser.indexOf('chrome') > -1) {
          browser = 1; // Chrome
        } else {
          browser = 'safari'; // Safari
        }
      }

      if (node.innerHTML.includes('mso-list:\nIgnore')) {
        node.innerHTML = node.innerHTML.replace(/mso-list:\nIgnore/gi, 'mso-list:Ignore');
      }

      var list_type_node = node.querySelector('span[style="mso-list:Ignore"]'); //this is added to check the browser is safari as we are not getting html same as chrome

      if (list_type_node == null && browser == 'safari') {
        list_type_node = node.querySelector('span[lang="PT-BR"]');
      }

      var contents;
      var listObj;
      var list_tag;
      var listStyle;
      var startIndexUpperAlpha = 64;
      var startIndexLowerAlpha = 96; // Checking the list is ordered or unordered

      if (list_type_node) {
        is_ordered = is_ordered || order_regex.test(list_type_node.textContent);
      }

      var listType;
      if (list_type_node !== null) listType = list_type_node.textContent.trim().split('.')[0]; // Get the list type
      // const list_tag = is_ordered ? 'ol' : 'ul'

      if (is_ordered == true) {
        listType = list_type_node.textContent.trim().split('.')[0];

        if (listType == '1') {
          listStyle = 'decimal;';
        } else if (listType == 'i') {
          listStyle = 'lower-roman;';
        } else if (listType == 'I') {
          listStyle = 'upper-roman;';
        } else if (listType == 'o') {
          listStyle = 'circle;';
        } //https://github.com/froala-labs/froala-editor-js-2/issues/1887
        // to check the bullet lists
        else if (!listType.match(/^v$/)) {
            if (listType.match(/^[a-z]$/) || listType.match(/^[a-z]\)$/)) {
              listStyle = 'lower-alpha;';
            } else if (listType.match(/^[A-Z]$/) || listType.match(/^[A-Z]\)$/)) {
              listStyle = 'upper-alpha;';
            }
          }

        listStyle = 'list-style-type: ' + listStyle;
        list_tag = 'ol';
      } else {
        if (list_type_node != null) listType = list_type_node.textContent.trim().split('.')[0];

        if (listType == '§') {
          listStyle = 'square;';
        } else if (listType == "·") {
          listStyle = 'disc;';
        }

        listStyle = 'list-style-type: ' + listStyle;
        list_tag = 'ul';
      } // creating new list


      var classType = ''; // https://github.com/froala-labs/froala-editor-js-2/issues/1860

      if (list_type_node != undefined && list_type_node.textContent != undefined && !isNaN(parseInt(list_type_node.textContent.trim().split('.')[1], 10))) {
        classType = ' class="decimal_type" ';
      }

      var s; // https://github.com/froala-labs/froala-editor-js-2/issues/1887

      var next_level = _getListLevel(node);

      var margin = node.style.marginLeft;
      var size;

      if (margin.includes('in')) {
        size = 'in';
        margin = parseFloat(margin) - 0.5;
      } else if (margin.includes('pt')) {
        size = 'px';
        margin = parseFloat(margin) - 10;
      }

      if (next_level == 1) {
        s = listStyle ? '<' + list_tag + ' style = "' + listStyle + '; margin-left:' + margin + size + ';">' : '<' + list_tag + ' style="margin-left:' + margin + size + ';"' + '>'; // https://github.com/froala-labs/froala-editor-js-2/issues/1887

        if (listStyle == 'list-style-type: upper-alpha;') {
          var index = listType.charCodeAt(0) - startIndexUpperAlpha;
          s = listStyle ? '<' + list_tag + classType + ' start="' + index + '"' + ' style = "' + listStyle + ' margin-left:' + margin + size + ';">' : '<' + list_tag + '>';
        } else if (listStyle == 'list-style-type: lower-alpha;') {
          var _index = listType.charCodeAt(0) - startIndexLowerAlpha;

          s = listStyle ? '<' + list_tag + classType + ' start="' + _index + '"' + ' style = "' + listStyle + 'margin-left:' + margin + size + ';">' : '<' + list_tag + '>';
        } else {
          s = listStyle ? '<' + list_tag + classType + ' style = "' + listStyle + ';margin-left:' + margin + size + ';">' : '<' + list_tag + ' style="margin-left:' + margin + size + ';"' + '>';
        }
      } else {
        // https://github.com/froala-labs/froala-editor-js-2/issues/1887
        if (listStyle == 'list-style-type: upper-alpha;') {
          var _index2 = listType.charCodeAt(0) - startIndexUpperAlpha;

          s = listStyle ? '<' + list_tag + classType + ' style = "' + listStyle + ' start="' + _index2 + '">' : '<' + list_tag + '>';
        } else if (listStyle == 'list-style-type: lower-alpha;') {
          var _index3 = listType.charCodeAt(0) - startIndexLowerAlpha;

          s = listStyle ? '<' + list_tag + classType + ' style = "' + listStyle + ' start="' + _index3 + '">' : '<' + list_tag + '>';
        } else {
          s = listStyle ? '<' + list_tag + classType + ' style = "' + listStyle + '">' : '<' + list_tag + '>';
        }
      }

      var tagClosedFlag = false;

      while (node) {
        // Stop at first sibling that is not a list.
        if (!_isList(node)) {
          // Skip bookmarks.
          if (node.outerHTML && node.outerHTML.indexOf('mso-bookmark') > 0 && (node.textContent || '').length == 0) {
            node = node.nextElementSibling;
            continue;
          }

          break;
        } // getting level of next node


        var _next_level = _getListLevel(node); // Set the level if it's the first level or use the same


        level = level || _next_level; // Create new list if next node level is greater than current one

        if (_next_level > level) {
          listObj = _buildList(node, head_style_hash, _next_level, node.style.marginLeft);
          s += listObj.el.outerHTML; // Getting the subsequent node after creating new list

          node = listObj.currentNode; // Need to start over to check if next node might be on same level

          continue;
        } else if (_next_level < level) {
          // Lower level found. Current list is done.
          break;
        } else {
          // Checked list tag if levels are same.(https://github.com/froala/wysiwyg-editor/issues/3088)
          // Checking the order of next element.
          if (node.firstElementChild && node.firstElementChild.firstElementChild && node.firstElementChild.firstElementChild.firstChild) {
            order_regex.lastIndex = 0;
          } // Checking the order of current element.


          if (previous_element_sibling && previous_element_sibling.firstElementChild && previous_element_sibling.firstElementChild.firstElementChild && previous_element_sibling.firstElementChild.firstElementChild.firstChild) {
            order_regex.lastIndex = 0;
            prev_order = order_regex.test(previous_element_sibling.firstElementChild.firstElementChild.firstChild.data || previous_element_sibling.firstElementChild.firstElementChild.firstChild.firstChild && previous_element_sibling.firstElementChild.firstElementChild.firstChild.firstChild.data || '');
          } // If levels are same,we are comparing the order of the next element.
          // If the order is same it will append the element in existing list else will create a new list.
          // https://github.com/froala-labs/froala-editor-js-2/issues/1861
          // Added condition for ul and ol lists to differentiate the behavior of the list with different type of lists.


          var isMarginEqual = false;

          if (!prev_margin && !node.style.marginLeft || prev_margin && node.style.marginLeft && prev_margin === node.style.marginLeft) {
            isMarginEqual = true;
          }

          prev_margin = node.style.marginLeft;

          if (isMarginEqual || prev_order === undefined) {
            contents = _getListContent(node, head_style_hash); // https://github.com/froala-labs/froala-editor-js-2/issues/1860

            if (node.nextSibling.innerText != undefined && node.nextSibling.innerText != undefined && !s.includes('class="decimal_type"')) {
              if (!isNaN(parseInt(node.nextSibling.innerText.trim().split('.')[1], 10))) {
                s = s.substring(3, 0) + ' class="decimal_type"' + s.substring(3, s.length);
              }
            }

            s += '<li>' + contents + '</li>';
          } else {
            // https://github.com/froala-labs/froala-editor-js-2/issues/1861
            if (_next_level == 1) {
              s += '</' + list_tag + '>';
              tagClosedFlag = true;
              previous_element_sibling = null;
            }

            listObj = _buildList(node, head_style_hash, _next_level, node.style.marginLeft);
            s += listObj.el.outerHTML;
            node = listObj.currentNode;
          }
        } // Storing the next sibling in temporary variable


        var tmp = node && node.nextElementSibling; // Check if node is there get the previous element sibling

        if (tmp) {
          previous_element_sibling = tmp.previousElementSibling;
        } // https://github.com/froala-labs/froala-editor-js-2/issues/1854


        if (node && !_isList(node)) {
          // Skip bookmarks.
          if (node.outerHTML && node.outerHTML.indexOf('mso-bookmark') > 0 && (node.textContent || '').length == 0) {
            node = node.nextElementSibling;
            continue;
          }

          break;
        } // Remove the used node


        node && node.parentNode && node.parentNode.removeChild(node); // Restore the next sibling to node

        node = tmp;
      } // Finish list
      // https://github.com/froala-labs/froala-editor-js-2/issues/1861


      if (!tagClosedFlag) s += '</' + list_tag + '>'; // Convert string to node element.

      var div = document.createElement('div');
      div.innerHTML = s;
      var element = div; // Returning list element and current node

      return {
        el: element,
        currentNode: node
      };
    }

    function _getAllowedListStyles(node) {
      var styles = '';
      var allowedStyles = ['line-height', 'font-family', 'font-size', 'color', 'background'];
      var parentStyles = node.getAttribute('style');

      if (parentStyles) {
        allowedStyles.forEach(function (style) {
          //https://github.com/froala-labs/froala-editor-js-2/issues/1852
          var foundVal = parentStyles.match(new RegExp(style + ':.*(;|)'));

          if (foundVal) {
            styles += foundVal[0] + ';';
          }
        });
      }

      return styles;
    }
    /*
     * Change tag name of an element.
     */


    function _changeTagName(old_node, tag_name) {
      var new_node = document.createElement(tag_name);

      for (var i = 0; i < old_node.attributes.length; i++) {
        var attribute = old_node.attributes[i].name;
        new_node.setAttribute(attribute, old_node.getAttribute(attribute));
      }

      new_node.innerHTML = old_node.innerHTML;
      old_node.parentNode.replaceChild(new_node, old_node);
      return new_node;
    }
    /*
     * Clean tr element.
     */


    function _cleanTr(tr, head_style_hash) {
      // Clean tr attributes.
      editor.node.clearAttributes(tr); // Get first child.

      var child = tr.firstElementChild; // Total table width.

      var total_width = 0; // Tell if at least one child has a missing width.

      var missing_width = false; // Width attribute.

      var width_attr = null; // Clean td childs and calculate total table width.

      while (child) {
        // Cleanup w: tags.
        if (child.firstElementChild && child.firstElementChild.tagName.indexOf('W:') !== -1) {
          child.innerHTML = child.firstElementChild.innerHTML;
        } // Add width to total.


        width_attr = child.getAttribute('width');

        if (!width_attr && !missing_width) {
          missing_width = true;
        }

        total_width += parseInt(width_attr, 10); // Replace to <br> childs that are empty or &nbsp.

        if (!child.firstChild || child.firstChild && child.firstChild.data === FE.UNICODE_NBSP) {
          if (child.firstChild) {
            _removeNode(child.firstChild);
          }

          child.innerHTML = '<br>';
        }

        var td_child = child.firstElementChild; // If child has more than one children, it means that every child has its own alignment.

        var has_single_child = child.children.length === 1; // Change p to span or div and clean alignment on every element child.

        while (td_child) {
          if (td_child.tagName === 'P' && !_isList(td_child)) {
            // Set alignment to td parent.
            if (has_single_child) {
              _cleanAlignment(td_child);
            }
          } // Move to next element sibling.


          td_child = td_child.nextElementSibling;
        } // Add styles from head.


        if (head_style_hash) {
          // Style from .xl classes.
          // Get class from child.
          var class_attr = child.getAttribute('class');

          if (class_attr) {
            class_attr = _normalizeAttribute(class_attr); // Match xl class.

            var class_matches = class_attr.match(/xl[0-9]+/gi);

            if (class_matches) {
              var xl_class = class_matches[0];
              var dot_xl_class = '.' + xl_class;

              if (head_style_hash[dot_xl_class]) {
                _appendStyle(child, head_style_hash[dot_xl_class]);
              }
            }
          } // Style from td.


          if (head_style_hash.td) {
            _appendStyle(child, head_style_hash.td);
          }
        }

        var style = child.getAttribute('style');

        if (style) {
          style = _normalizeAttribute(style); // Add semicolon, if it is missing, to the end of current style.

          if (style && style.slice(-1) !== ';') {
            style += ';';
          }
        } // Store valign attribute.


        var valign = child.getAttribute('valign');

        if (!valign && style) {
          var valign_matches = style.match(/vertical-align:.+?[; "]{1,1}/gi);

          if (valign_matches) {
            valign = valign_matches[valign_matches.length - 1].replace(/vertical-align:(.+?)[; "]{1,1}/gi, '$1');
          }
        } // Store text-align style attribute.


        var halign = null;

        if (style) {
          var halign_matches = style.match(/text-align:.+?[; "]{1,1}/gi);

          if (halign_matches) {
            halign = halign_matches[halign_matches.length - 1].replace(/text-align:(.+?)[; "]{1,1}/gi, '$1');
          }

          if (halign === 'general') {
            halign = null;
          }
        } // Store background color style attribute.


        var background_color = null;

        if (style) {
          var background_matches = style.match(/background:.+?[; "]{1,1}/gi);

          if (background_matches) {
            background_color = background_matches[background_matches.length - 1].replace(/background:(.+?)[; "]{1,1}/gi, '$1');
          }
        } // Store colspan.


        var colspan = child.getAttribute('colspan'); // Store rowspan.

        var rowspan = child.getAttribute('rowspan'); // Restore colspan.

        if (colspan) {
          child.setAttribute('colspan', colspan);
        } // Restore rowspan.


        if (rowspan) {
          child.setAttribute('rowspan', rowspan);
        } // Add valign to style.


        if (valign) {
          child.style['vertical-align'] = valign;
        } // Add horizontal align to style.


        if (halign) {
          child.style['text-align'] = halign;
        } // Add background color to style.


        if (background_color) {
          child.style['background-color'] = background_color;
        } // Set the width again.


        if (width_attr) {
          child.setAttribute('width', width_attr);
        } // Move to next sibling.


        child = child.nextElementSibling;
      } // Get first child again.


      child = tr.firstElementChild; // Set the width in percentage to every child.

      while (child) {
        width_attr = child.getAttribute('width');

        if (missing_width) {
          // Remove width.
          child.removeAttribute('width');
        } else {
          // Set the width considering that every child has equal widths.
          child.setAttribute('width', parseInt(width_attr, 10) * 100 / total_width + '%');
        } // Move to next sibling.


        child = child.nextElementSibling;
      }
    }
    /*
     * Clean align attribute.
     */


    function _cleanAlignment(el) {
      var align = el.getAttribute('align');

      if (align) {
        el.style['text-align'] = align;
        el.removeAttribute('align');
      }
    }
    /*
     * Clean up atribute.
     */


    function _normalizeAttribute(attribute) {
      return attribute.replace(/\n|\r|\n\r|&quot;/g, '');
    }
    /*
     * Append style to element.
     */


    function _appendStyle(el, style, last) {
      if (!style) {
        return;
      } // Get current element style.


      var old_style = el.getAttribute('style'); // Add semicolon, if it is missing, to the end of current style.

      if (old_style && old_style.slice(-1) !== ';') {
        old_style += ';';
      } // Add semicolon, if it is missing, to the end of current style.


      if (style && style.slice(-1) !== ';') {
        style += ';';
      } // Remove newlines.


      style = style.replace(/\n/gi, ''); // Append at the begining or at the end.

      var new_style = null;

      if (last) {
        new_style = (old_style || '') + style;
      } else {
        new_style = style + (old_style || '');
      }

      el.setAttribute('style', new_style);
    }
    /*
     * Delete duplicate attributes found on style. Keep the last one.
     */


    function _cleanStyleDuplicates(el) {
      var style = el.getAttribute('style');

      if (!style) {
        return;
      }

      style = _normalizeAttribute(style); // Add semicolon, if it is missing, to the end of style.

      if (style && style.slice(-1) !== ';') {
        style += ';';
      } // Get styles: attr:value


      var style_list = style.match(/(^|\S+?):.+?;{1,1}/gi);

      if (!style_list) {
        return;
      } // Key = attribute. Value = attribute's value. Duplicate keys will be overrided.


      var style_hash = {};

      for (var i = 0; i < style_list.length; i++) {
        var style_list_item = style_list[i];
        var splited_style = style_list_item.split(':');

        if (splited_style.length !== 2) {
          continue;
        } // Add style to hash without text-align on span.


        if (!(splited_style[0] === 'text-align' && el.tagName === 'SPAN')) {
          style_hash[splited_style[0]] = splited_style[1];
        }
      } // Create the new style without duplicates.


      var new_style = '';

      for (var attr in style_hash) {
        if (style_hash.hasOwnProperty(attr)) {
          // Change font-size form pt to px
          if (attr === 'font-size' && style_hash[attr].slice(-3) === 'pt;') {
            var number = null;

            try {
              number = parseFloat(style_hash[attr].slice(0, -3), 10);
            } catch (e) {
              number = null;
            }

            if (number) {
              number = Math.round(1.33 * number);
              style_hash[attr] = number + 'px;';
            }
          }

          new_style += attr + ':' + style_hash[attr];
        }
      }

      if (new_style) {
        el.setAttribute('style', new_style);
      }
    }
    /*
     * Convert a hex string to base64.
     */


    function _hexToBase64(hex) {
      var hexa_chars = hex.match(/[0-9a-f]{2}/gi);
      var dec_chars = [];

      for (var i = 0; i < hexa_chars.length; i++) {
        dec_chars.push(String.fromCharCode(parseInt(hexa_chars[i], 16)));
      }

      var dec = dec_chars.join('');
      return btoa(dec);
    }

    var _rtf_map = null;

    function _getRtfData(rtf, letter, p_type) {
      var imgs = rtf.split(p_type);

      for (var i = 1; i < imgs.length; i++) {
        var img_data = imgs[i];
        img_data = img_data.split('shplid');

        if (img_data.length > 1) {
          img_data = img_data[1];
          var id = '';
          var t = 0;

          while (t < img_data.length) {
            if (img_data[t] === '\\' || img_data[t] === '{' || img_data[t] === ' ' || img_data[t] === '\r' || img_data[t] === '\n') {
              break;
            }

            id += img_data[t];
            t++;
          }

          var bliptab_split = img_data.split('bliptag');

          if (bliptab_split && bliptab_split.length < 2) {
            continue;
          }

          var image_type = null;

          if (bliptab_split[0].indexOf('pngblip') !== -1) {
            image_type = 'image/png';
          } else if (bliptab_split[0].indexOf('jpegblip') !== -1) {
            image_type = 'image/jpeg';
          }

          if (!image_type) {
            continue;
          }

          var bracket_split = bliptab_split[1].split('}');

          if (bracket_split && bracket_split.length < 2) {
            continue;
          }

          var space_split = void 0;

          if (bracket_split.length > 2 && bracket_split[0].indexOf('blipuid') !== -1) {
            space_split = bracket_split[1].split(' ');
          } else {
            space_split = bracket_split[0].split(' ');

            if (space_split && space_split.length < 2) {
              continue;
            }

            space_split.shift();
          }

          var image_hex = space_split.join('');
          _rtf_map[letter + id] = {
            image_hex: image_hex,
            image_type: image_type
          };
        }
      }
    }

    function _buildRtfMap(rtf) {
      _rtf_map = {};

      _getRtfData(rtf, 'i', '\\shppict');

      _getRtfData(rtf, 's', '\\shp{');
    }
    /*
     * Clean HTML Image.
     */


    function _cleanImage(el, rtf) {
      if (!rtf) {
        return;
      } // vshapes_tag will identify the image in rtf.


      var vshapes_tag; // Image case.

      if (el.tagName === 'IMG') {
        // Get src.
        var src = el.getAttribute('src');

        if (!src || src.indexOf('file://') === -1) {
          return;
        } else if (src.indexOf('file://') === 0) {
          if (editor.helpers.isURL(el.getAttribute('alt'))) {
            el.setAttribute('src', el.getAttribute('alt'));
            return;
          }
        } // vshapes_tag will identify the image in rtf.


        vshapes_tag = _v_shapes_map[el.getAttribute('v:shapes')];

        if (!vshapes_tag) {
          vshapes_tag = el.getAttribute('v:shapes'); // Disregard formulas.

          if (el.parentNode && el.parentNode.parentNode && el.parentNode.parentNode.innerHTML.indexOf('msEquation') >= 0) {
            vshapes_tag = null;
          }
        }
      } else {
        vshapes_tag = el.parentNode.getAttribute('o:spid');
      }

      el.removeAttribute('height');

      if (!vshapes_tag) {
        return;
      }

      _buildRtfMap(rtf);

      var img_data = _rtf_map[vshapes_tag.substring(7)];

      if (img_data) {
        // Convert image hex to base64.
        var image_base64 = _hexToBase64(img_data.image_hex); // Build data uri.


        var data_uri = 'data:' + img_data.image_type + ';base64,' + image_base64;

        if (el.tagName === 'IMG') {
          el.src = data_uri;
          el.setAttribute('data-fr-image-pasted', true);
        } else {
          $(el.parentNode).before('<img data-fr-image-pasted="true" src="' + data_uri + '" style="' + el.parentNode.getAttribute('style') + '">').remove();
        }
      }
    }
    /*
     * Clean element.
     */


    function _cleanElement(el, head_style_hash) {
      var tag_name = el.tagName;
      var tag_name_lower_case = tag_name.toLowerCase(); // Check if we need to change a tag. Tags should be changed only from parent.

      if (el.firstElementChild) {
        // Change i to em.
        if (el.firstElementChild.tagName === 'I') {
          _changeTagName(el.firstElementChild, 'em'); // Change b to strong.

        } else if (el.firstElementChild.tagName === 'B') {
          _changeTagName(el.firstElementChild, 'strong');
        }
      } // Remove no needed tags.


      var word_tags = ['SCRIPT', 'APPLET', 'EMBED', 'NOFRAMES', 'NOSCRIPT'];

      if (word_tags.indexOf(tag_name) !== -1) {
        _removeNode(el);

        return false;
      } // Check single spaces.
      // if (tag_name === 'O:P' && el.innerHTML === '&nbsp') {
      //   el.innerHTML = FE.INVISIBLE_SPACE
      // }
      // Remove tags but keep content.


      var ignore_tags = ['META', 'LINK', 'XML', 'ST1:', 'O:', 'W:', 'FONT'];

      for (var i = 0; i < ignore_tags.length; i++) {
        if (tag_name.indexOf(ignore_tags[i]) !== -1) {
          if (el.innerHTML) {
            el.outerHTML = el.innerHTML;

            _removeNode(el);

            return false;
          } else {
            // Remove if does not have content.
            _removeNode(el);

            return false;
          }
        }
      } // Add class style from head.


      if (tag_name !== 'TD') {
        var class_attr = el.getAttribute('class') || 'MsoNormal';

        if (head_style_hash && class_attr) {
          class_attr = _normalizeAttribute(class_attr);
          var class_contents = class_attr.split(' '); // All classes.

          for (var _i = 0; _i < class_contents.length; _i++) {
            var class_content = class_contents[_i]; // Create style attributes list.

            var style_attrs = []; // Only classes.

            var style_attr = '.' + class_content;
            style_attrs.push(style_attr); // Classes under tag.

            style_attr = tag_name_lower_case + style_attr;
            style_attrs.push(style_attr);

            for (var j = 0; j < style_attrs.length; j++) {
              if (head_style_hash[style_attrs[j]]) {
                _appendStyle(el, head_style_hash[style_attrs[j]]);
              }
            }
          }

          el.removeAttribute('class');
        } // Add tag style from head.


        if (head_style_hash && head_style_hash[tag_name_lower_case]) {
          _appendStyle(el, head_style_hash[tag_name_lower_case]);
        }
      } // Wrap paragraphs inner html in a span.


      var paragraph_tag_list = ['P', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'PRE'];

      if (paragraph_tag_list.indexOf(tag_name) !== -1) {
        // Set style from head.
        var el_class = el.getAttribute('class');

        if (el_class) {
          if (head_style_hash && head_style_hash[tag_name.toLowerCase() + '.' + el_class]) {
            _appendStyle(el, head_style_hash[tag_name.toLowerCase() + '.' + el_class]);
          } // Remove mso values from class.


          if (el_class.toLowerCase().indexOf('mso') !== -1) {
            var cleaned_class = _normalizeAttribute(el_class);

            cleaned_class = cleaned_class.replace(/[0-9a-z-_]*mso[0-9a-z-_]*/gi, '');

            if (cleaned_class) {
              el.setAttribute('class', cleaned_class);
            } else {
              el.removeAttribute('class');
            }
          }
        } // keep only text-align in style.


        var paragraph_style = el.getAttribute('style');

        if (paragraph_style) {
          var paragraph_style_matches = paragraph_style.match(/text-align:.+?[; "]{1,1}/gi);

          if (paragraph_style_matches) {
            paragraph_style_matches[paragraph_style_matches.length - 1].replace(/(text-align:.+?[; "]{1,1})/gi, '$1');
          }
        }

        _cleanAlignment(el);
      } // Clean tr.


      if (tag_name === 'TR') {
        _cleanTr(el, head_style_hash);
      } // Clean empty links.


      if (tag_name === 'A' && !el.attributes.getNamedItem('href') && !el.attributes.getNamedItem('name') && el.innerHTML) {
        el.outerHTML = el.innerHTML;
      } // https://github.com/froala/wysiwyg-editor/issues/3272


      if (tag_name == 'A' && el.getAttribute('href') && el.querySelector('img')) {
        // removing empty span tags
        var spanTags = el.querySelectorAll('span');

        for (var _i2 = 0; _i2 < spanTags.length; _i2++) {
          if (!spanTags[_i2].innerText) {
            spanTags[_i2].outerHTML = spanTags[_i2].innerHTML;
          }
        }
      } // Keep empty TH and TD.


      if ((tag_name === 'TD' || tag_name === 'TH') && !el.innerHTML) {
        el.innerHTML = '<br>';
      } // Clean table.


      if (tag_name === 'TABLE') {
        el.style.width = el.style.width;
      } // Remove lang attribute.


      if (el.getAttribute('lang')) {
        el.removeAttribute('lang');
      } // Remove mso values from style.


      if (el.getAttribute('style') && el.getAttribute('style').toLowerCase().indexOf('mso') !== -1) {
        var cleaned_style = _normalizeAttribute(el.getAttribute('style'));

        cleaned_style = cleaned_style.replace(/[0-9a-z-_]*mso[0-9a-z-_]*:.+?(;{1,1}|$)/gi, '');

        if (cleaned_style) {
          el.setAttribute('style', cleaned_style);
        } else {
          el.removeAttribute('style');
        }
      }

      return true;
    }
    /*
     * Parse styles from head and return them into a hash.
     */


    function _parseHeadStyle(head) {
      var head_style_hash = {};
      var head_styles = head.getElementsByTagName('style');

      if (head_styles.length) {
        var head_style = head_styles[0]; // Match styles.

        var style_list = head_style.innerHTML.match(/[\S ]+\s+{[\s\S]+?}/gi);

        if (style_list) {
          for (var i = 0; i < style_list.length; i++) {
            var style = style_list[i]; // Get style attributes.

            var style_attrs = style.replace(/([\S ]+\s+){[\s\S]+?}/gi, '$1'); // Get style definitions.

            var style_definitions = style.replace(/[\S ]+\s+{([\s\S]+?)}/gi, '$1'); // Trim whitespaces.

            style_attrs = style_attrs.replace(/^[\s]|[\s]$/gm, '');
            style_definitions = style_definitions.replace(/^[\s]|[\s]$/gm, ''); // Trim new lines.

            style_attrs = style_attrs.replace(/\n|\r|\n\r/g, '');
            style_definitions = style_definitions.replace(/\n|\r|\n\r/g, '');
            var style_attrs_array = style_attrs.split(', '); // Add every attribute to hash.

            for (var j = 0; j < style_attrs_array.length; j++) {
              head_style_hash[style_attrs_array[j]] = style_definitions;
            }
          }
        }
      }

      return head_style_hash;
    }
    /**
     * Create a map with the ID for images.
     */


    function _getVShapes(html) {
      var splits = html.split('v:shape');

      for (var i = 1; i < splits.length; i++) {
        var split = splits[i];
        var id = split.split(' id="')[1];

        if (id && id.length > 1) {
          id = id.split('"')[0];
          var oid = split.split(' o:spid="')[1];

          if (oid && oid.length > 1) {
            oid = oid.split('"')[0];
            _v_shapes_map[id] = oid;
          }
        }
      }
    }
    /*
     * Clean HTML that was pasted from Word.
     */


    function _wordClean(html, rtf) {
      // Remove junk from outside html.
      if (html.indexOf('<html') >= 0) {
        html = html.replace(/[.\s\S\w\W<>]*(<html[^>]*>[.\s\S\w\W<>]*<\/html>)[.\s\S\w\W<>]*/i, '$1');
      } // Get the vshapes for images.


      _getVShapes(html); // Convert string into document.


      var parser = new DOMParser();
      var word_doc = parser.parseFromString(html, 'text/html');
      var head = word_doc.head;
      var body = word_doc.body; // Create style attrs hash.

      var head_style_hash = _parseHeadStyle(head); // Remove text nodes that do not contain non-whitespace characters and has new lines in them.


      _traverse(body, function (node) {
        if (node.nodeType === Node.TEXT_NODE && /\n|\u00a0|\r/.test(node.data)) {
          // https://github.com/froala/wysiwyg-editor/issues/3298
          // https://github.com/froala/wysiwyg-editor/issues/3327
          // if has no breaking space keep it
          // 2nd condition to check no break spaces
          if (!/\S| /.test(node.data) && !/[\u00a0]+/.test(node.data)) {
            // Keep single &nbsp
            if (node.data === FE.UNICODE_NBSP) {
              node.data = "\u200B";
              return true;
            }

            if (node.data.length === 1 && node.data.charCodeAt(0) === 10) {
              node.data = ' ';
              return true;
            }

            _removeNode(node);

            return false;
          } // Remove newlines.
          else {
              node.data = node.data.replace(/\n|\r/gi, ' ');
            }
        }

        return true;
      }); // Process images.


      _traverse(body, function (node) {
        // Element node.
        if (node.nodeType === Node.ELEMENT_NODE && (node.tagName === 'V:IMAGEDATA' || node.tagName === 'IMG')) {
          _cleanImage(node, rtf);
        }

        return true;
      }); // Process lists.


      var lists = body.querySelectorAll('ul > ul, ul > ol, ol > ul, ol > ol');

      for (var i = lists.length - 1; i >= 0; i--) {
        if (lists[i].previousElementSibling && lists[i].previousElementSibling.tagName === 'LI') {
          lists[i].previousElementSibling.appendChild(lists[i]);
        }
      } // Clean the body.


      _traverse(body, function (node) {
        // Text node.
        if (node.nodeType === Node.TEXT_NODE) {
          // https://github.com/froala/wysiwyg-editor/issues/1364.
          node.data = node.data.replace(/<br>(\n|\r)/gi, '<br>');
          return false;
        } // Element node.
        else if (node.nodeType === Node.ELEMENT_NODE) {
            // List found.
            if (_isList(node)) {
              // Keep the parent node and previous sibling because the node could be deleted in the list building.
              var parent_node = node.parentNode;
              var previous_sibling = node.previousSibling; // Get list element.

              var list_element = _buildList(node, head_style_hash).el; // Find the element to insert the new list before it.


              var before_element = null; // Current node was not the first.

              if (previous_sibling) {
                before_element = previous_sibling.nextSibling;
              } else {
                before_element = parent_node.firstChild;
              } // Insert before.


              if (before_element) {
                parent_node.insertBefore(list_element, before_element);
              } // Push to the end.
              else {
                  parent_node.appendChild(list_element);
                }

              return false;
            } else {
              if (node.tagName === 'FONT' && head_style_hash['.' + node.getAttribute('class')]) {
                node = _changeTagName(node, 'span');
              }

              return _cleanElement(node, head_style_hash);
            }
          } // Comment node.
          else if (node.nodeType === Node.COMMENT_NODE) {
              // removing the extra line breaks in comments
              if (node.data.indexOf('[if !supportLineBreakNewLine]') > -1) {
                var nextNode = node.nextSibling;

                while (nextNode) {
                  nextNode = node.nextSibling;
                  nextNode && _removeNode(nextNode);

                  if (nextNode.data && nextNode.data.indexOf('[endif]') > -1) {
                    nextNode = null;
                  }
                }
              } //https://github.com/froala-labs/froala-editor-js-2/issues/1859


              if (node.data.indexOf('[if supportFields]') > -1) {
                if (node.data.indexOf('FORMCHECKBOX') > -1) {
                  var checkbox = document.createElement('input');
                  checkbox.type = "checkbox";
                  node.parentNode.insertBefore(checkbox, node.nextSibling);
                }
              }

              _removeNode(node);

              return false;
            }

        return true;
      }); // Remove empty tags and clean duplicate styles.


      _traverse(body, function (node) {
        // Element node.
        if (node.nodeType === Node.ELEMENT_NODE) {
          var tag_name = node.tagName; // Empty. Skip br tag.
          // https://github.com/froala-labs/froala-editor-js-2/issues/1859

          if (!node.innerHTML && ['BR', 'IMG', 'INPUT'].indexOf(tag_name) === -1) {
            var parent = node.parentNode; // Remove recursively.

            while (parent) {
              _removeNode(node);

              node = parent; // Stop when non-empty element is found.

              if (node.innerHTML) {
                break;
              }

              parent = node.parentNode;
            }

            return false;
          } else {
            _cleanStyleDuplicates(node);
          }
        }

        return true;
      }); // https://github.com/froala/wysiwyg-editor/issues/3098, Remove empty anchor tags


      _traverse(body, function (node) {
        // remove anchor tag if it doesn't have url
        if (node && node.nodeName === 'A' && node.href === '') {
          // replace parent a tag with its child nodes
          var fragment = document.createDocumentFragment();

          while (node.firstChild) {
            fragment.appendChild(node.firstChild);
          }

          node.parentNode.replaceChild(fragment, node);
        }

        return true;
      }); // Converd document to string.


      var word_doc_string = body.outerHTML; // Clean HTML.

      var htmlAllowedStylePropsCopy = editor.opts.htmlAllowedStyleProps;
      editor.opts.htmlAllowedStyleProps = editor.opts.wordAllowedStyleProps;
      word_doc_string = editor.clean.html(word_doc_string, editor.opts.wordDeniedTags, editor.opts.wordDeniedAttrs, false);
      editor.opts.htmlAllowedStyleProps = htmlAllowedStylePropsCopy;
      return word_doc_string;
    }

    return {
      _init: _init,
      clean: clean,
      _wordClean: _wordClean
    };
  };

})));
//# sourceMappingURL=word_paste.js.map
