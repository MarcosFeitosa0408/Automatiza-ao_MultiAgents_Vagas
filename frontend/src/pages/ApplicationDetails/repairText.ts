// Recupera sequências de UTF-8 lidas como Latin-1/Windows-1252.
// Preserva texto correto, emojis e caracteres perdidos (�).
export function repairText(original: string): string {
  const extras: Record<string, number> = {
    "€": 128, "‚": 130, "ƒ": 131, "„": 132, "…": 133,
    "†": 134, "‡": 135, "ˆ": 136, "‰": 137, "Š": 138,
    "‹": 139, "Œ": 140, "Ž": 142, "‘": 145, "’": 146,
    "“": 147, "”": 148, "•": 149, "–": 150, "—": 151,
    "˜": 152, "™": 153, "š": 154, "›": 155, "œ": 156,
    "ž": 158, "Ÿ": 159,
  };
  const decoder = new TextDecoder("utf-8", { fatal: true });
  const byteOf = (char: string): number =>
    extras[char] ?? char.codePointAt(0)!;

  let result = original;

  for (let round = 0; round < 2; round++) {
    const chars = Array.from(result);
    let repaired = "";

    for (let index = 0; index < chars.length;) {
      const first = byteOf(chars[index]);
      const length =
        first >= 0xc2 && first <= 0xdf ? 2 :
        first >= 0xe0 && first <= 0xef ? 3 :
        first >= 0xf0 && first <= 0xf4 ? 4 : 0;

      if (length && index + length <= chars.length) {
        const bytes = chars.slice(index, index + length).map(byteOf);
        const validContinuation = bytes.slice(1).every(
          (byte) => byte >= 0x80 && byte <= 0xbf,
        );

        if (validContinuation) {
          try {
            repaired += decoder.decode(new Uint8Array(bytes));
            index += length;
            continue;
          } catch {
            // Sequência inválida: preserva o caractere original.
          }
        }
      }

      repaired += chars[index];
      index++;
    }

    if (repaired === result) break;
    result = repaired;
  }

  return result;
}

export function hasLongRequirements(values: string[]): boolean {
  return values.some((value) => value.length > 300);
}
