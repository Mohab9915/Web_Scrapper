declare module 'caseless' {
  interface CaselessObject {
    [key: string]: any;
  }

  interface Caseless {
    set(name: string, value: any, clobber?: boolean): boolean;
    set(object: CaselessObject, clobber?: boolean): boolean;
    get(name: string): any;
    swap(name: string): string | undefined;
    has(name: string): boolean;
    delete(name: string): boolean;
  }

  function caseless(obj?: CaselessObject): Caseless;

  export = caseless;
}
