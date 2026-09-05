---
layout: archive
title: "Sitemap"
description: "Human-readable sitemap for chojecki.net, the personal website of Patryk Chojecki."
excerpt: "Human-readable sitemap for chojecki.net, the personal website of Patryk Chojecki."
permalink: /sitemap/
author_profile: true
---

{% include base_path %}

A list of all the posts and pages found on the site. For you robots out there is an [XML version]({{ base_path }}/sitemap.xml) available for digesting as well.

{% capture page_entries %}
{% for post in site.pages %}
  {% if post.title and post.layout != "redirect" %}
    {% unless post.sitemap == false or post.robots contains "noindex" %}
      {% include archive-single.html %}
    {% endunless %}
  {% endif %}
{% endfor %}
{% endcapture %}
{% assign page_entries = page_entries | strip %}
{% if page_entries != empty %}
<h2>Pages</h2>
{{ page_entries }}
{% endif %}

{% for collection in site.collections %}
  {% if collection.output %}
    {% assign documents = collection.docs %}
    {% assign display_label = collection.label | capitalize %}
    {% if collection.label == "portfolio" %}
      {% assign documents = documents | sort: "order" %}
      {% assign display_label = "Projects" %}
    {% endif %}
    {% capture collection_entries %}
      {% for post in documents %}
        {% unless post.sitemap == false or post.robots contains "noindex" %}
          {% include archive-single.html %}
        {% endunless %}
      {% endfor %}
    {% endcapture %}
    {% assign collection_entries = collection_entries | strip %}
    {% if collection_entries != empty %}
      <h2>{{ display_label }}</h2>
      {{ collection_entries }}
    {% endif %}
  {% endif %}
{% endfor %}
