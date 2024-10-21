import html
import re
from httpx import AsyncClient
from html.parser import HTMLParser
from typing import Optional
from atproto import models

from pyrogram.parser import utils

from init import logs


class ParserModel(models.AppBskyRichtextFacet.Main):
    index: Optional[str] = None
    offset: int
    length: int

    def get_origin(self) -> "models.AppBskyRichtextFacet.Main":
        index = models.AppBskyRichtextFacet.ByteSlice(
            byte_start=self.offset, byte_end=self.offset + self.length
        )
        return models.AppBskyRichtextFacet.Main(features=self.features, index=index)

    @staticmethod
    def from_origin(origin: "models.AppBskyRichtextFacet.Main") -> "ParserModel":
        return ParserModel(
            features=origin.features,
            offset=origin.index.byte_start,
            length=origin.index.byte_end - origin.index.byte_start,
        )


class Parser(HTMLParser):
    MENTION_RE = re.compile(r"bsky\.app/profile/([^/]+)")

    def __init__(self):
        super().__init__()

        self.text = ""
        self.facts: list[ParserModel] = []
        self.tag_entities = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        extra = {}

        if tag == "a":
            url = attrs.get("href", "")

            mention = Parser.MENTION_RE.match(url)

            if mention:
                entity = models.AppBskyRichtextFacet.Mention
                extra["did"] = mention.group(1)
            else:
                entity = models.AppBskyRichtextFacet.Link
                extra["uri"] = url
        else:
            return

        if tag not in self.tag_entities:
            self.tag_entities[tag] = []

        e = ParserModel(
            features=[entity(**extra)],
            offset=len(self.text.encode("utf-8")),
            length=0,
        )
        self.tag_entities[tag].append(e)

    def handle_data(self, data):
        data = html.unescape(data)

        for entities in self.tag_entities.values():
            for entity in entities:
                entity.length += len(data.encode("utf-8"))

        self.text += data

    def handle_endtag(self, tag):
        try:
            self.facts.append(self.tag_entities[tag].pop())
        except (KeyError, IndexError):
            line, offset = self.getpos()
            offset += 1

            logs.debug("Unmatched closing tag </%s> at line %s:%s", tag, line, offset)
        else:
            if not self.tag_entities[tag]:
                self.tag_entities.pop(tag)

    def error(self, message):
        pass


class HTML:
    def __init__(self):
        self.client = AsyncClient()

    async def resolve_peer(self, handle: str) -> Optional[str]:
        try:
            req = await self.client.get(
                "https://bsky.social/xrpc/com.atproto.identity.resolveHandle",
                params={"handle": handle},
                timeout=10,
            )
            req.raise_for_status()
            return req.json()["did"]
        except Exception:
            return None

    async def parse(self, text: str) -> dict:
        # Strip whitespaces from the beginning and the end, but preserve closing tags
        text = re.sub(r"^\s*(<[\w<>=\s\"]*>)\s*", r"\1", text)
        text = re.sub(r"\s*(</[\w</>]*>)\s*$", r"\1", text)

        parser = Parser()
        parser.feed(utils.add_surrogates(text))
        parser.close()

        if parser.tag_entities:
            unclosed_tags = []

            for tag, entities in parser.tag_entities.items():
                unclosed_tags.append(f"<{tag}> (x{len(entities)})")

            logs.info("Unclosed tags: %s", ", ".join(unclosed_tags))

        entities = []

        for fact in parser.facts:
            entity = fact.features[0]
            if isinstance(entity, models.AppBskyRichtextFacet.Mention):
                if not entity.did.startswith("did:plc:"):
                    did = await self.resolve_peer(entity.did)
                    if did:
                        entity = models.AppBskyRichtextFacet.Mention(did=did)
                    else:
                        continue

            fact.features[0] = entity
            entities.append(fact)

        # Remove zero-length entities
        entities = list(filter(lambda x: x.length > 0, entities))
        entities = sorted(entities, key=lambda e: e.offset) or None
        # get origin facts
        facets = [fact.get_origin() for fact in entities] if entities else None

        return {
            "message": utils.remove_surrogates(parser.text),
            "facets": facets,
        }

    @staticmethod
    def unparse(text: str, facets: list["models.AppBskyRichtextFacet.Main"]) -> str:
        entities = [ParserModel.from_origin(fact) for fact in facets]

        def parse_one(entity: ParserModel):
            """
            Parses a single entity and returns (start_tag, start), (end_tag, end)
            """
            fact = entity.features[0]
            start = entity.offset
            end = start + entity.length

            if isinstance(fact, models.AppBskyRichtextFacet.Link):
                url = fact.uri
                start_tag = f'<a href="{url}">'
                end_tag = "</a>"
            elif isinstance(fact, models.AppBskyRichtextFacet.Mention):
                did = fact.did
                url = "https://bsky.app/profile/" + did
                start_tag = f'<a href="{url}">'
                end_tag = "</a>"
            else:
                return

            return (start_tag, start), (end_tag, end)

        def recursive(entity_i: int) -> int:
            """
            Takes the index of the entity to start parsing from, returns the number of parsed entities inside it.
            Uses entities_offsets as a stack, pushing (start_tag, start) first, then parsing nested entities,
            and finally pushing (end_tag, end) to the stack.
            No need to sort at the end.
            """
            this = parse_one(entities[entity_i])
            if this is None:
                return 1
            (start_tag, start), (end_tag, end) = this
            entities_offsets.append((start_tag, start))
            internal_i = entity_i + 1
            # while the next entity is inside the current one, keep parsing
            while internal_i < len(entities) and entities[internal_i].offset < end:
                internal_i += recursive(internal_i)
            entities_offsets.append((end_tag, end))
            return internal_i - entity_i

        entities_offsets = []

        # probably useless because entities are already sorted by telegram
        entities.sort(key=lambda e: (e.offset, -e.length))

        # main loop for first-level entities
        i = 0
        while i < len(entities):
            i += recursive(i)

        if entities_offsets:
            last_offset = entities_offsets[-1][1]
            # no need to sort, but still add entities starting from the end
            for entity, offset in reversed(entities_offsets):
                text = (
                    text.encode("utf-8")[:offset].decode("utf-8")
                    + entity
                    + html.escape(
                        text.encode("utf-8")[offset:last_offset].decode("utf-8")
                    )
                    + text.encode("utf-8")[last_offset:].decode("utf-8")
                )
                last_offset = offset

        return utils.remove_surrogates(text)


bsky_html_parser = HTML()
