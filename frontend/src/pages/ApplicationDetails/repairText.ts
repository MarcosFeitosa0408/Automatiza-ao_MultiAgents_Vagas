// Reverte apenas sequências reconhecíveis de UTF-8 lidas como Latin-1/Windows-1252.
// Não recupera caracteres perdidos (�), nem reescreve ou traduz o anúncio.
export function repairText(original: string): string {
  const extras: Record<string, number> = {"€":128,"‚":130,"ƒ":131,"„":132,"…":133,"†":134,"‡":135,"ˆ":136,"‰":137,"Š":138,"‹":139,"Œ":140,"Ž":142,"‘":145,"’":146,"“":147,"”":148,"•":149,"–":150,"—":151,"˜":152,"™":153,"š":154,"›":155,"œ":156,"ž":158,"Ÿ":159};
  const score = (text: string) => (text.match(/(?:Ã|Â)[\u0080-\u00bf]|â(?:€|[\u0080-\u00bf])/g) ?? []).length;
  let result = original;
  for (let round = 0; round < 2 && score(result) > 0; round++) {
    const bytes: number[] = [];
    for (const char of result) {
      const code = extras[char] ?? char.codePointAt(0)!;
      if (code > 255) return result;
      bytes.push(code);
    }
    try {
      const decoded = new TextDecoder("utf-8", { fatal: true }).decode(new Uint8Array(bytes));
      if (score(decoded) >= score(result)) break;
      result = decoded;
    } catch { break; }
  }
  return result;
}

export function hasLongRequirements(values: string[]): boolean {
  return values.some((value) => value.length > 300);
}
