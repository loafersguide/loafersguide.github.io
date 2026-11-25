-- Simple notes become inline-on-mobile sidenotes rather than a second copy.
-- Notes with richer block content stay as linked endnotes.
local number = 0
return {{Note = function(note)
  if #note.content ~= 1 or (note.content[1].t ~= 'Para' and note.content[1].t ~= 'Plain') then return end
  for _, x in ipairs(note.content[1].content) do
    if x.t == 'Link' or x.t == 'Note' or x.t == 'Image' then return end
  end
  number = number + 1
  local id = 'sidenote-' .. number
  local reference = pandoc.RawInline('html', '<sup class="sidenote-ref"><a href="#' .. id .. '" id="ref-' .. id .. '" aria-label="Note ' .. number .. '">' .. number .. '</a></sup>')
  local label = pandoc.RawInline('html','<span class="sidenote-number">' .. number .. '.</span> ')
  local content = pandoc.List({label})
  content:extend(note.content[1].content)
  content:insert(pandoc.RawInline('html', ' <a href="#ref-' .. id .. '" class="sidenote-back" aria-label="Back to note reference">↩</a>'))
  return {reference, pandoc.Span(content, pandoc.Attr(id, {'sidenote'}, {{'role', 'doc-footnote'}}))}
end}}
