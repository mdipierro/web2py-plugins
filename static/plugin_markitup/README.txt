Usage:
{{
response.files.append(URL('static','plugin_markitup/jquery.markitup.js'))
response.files.append(URL('static','plugin_markitup/sets/markmin/set.js'))
response.files.append(URL('static','plugin_markitup/skins/simple/style.css'))
response.files.append(URL('static','plugin_markitup/sets/markmin/style.css'))
}}
<script>
jQuery('textarea').markItUp(mySettings);
</script>



