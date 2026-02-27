export type ProtocoloStatus = "PENDING" | "WAITING_MAPPING" | "COMPLETED" | "ERROR";

export interface Protocolo {
  id: number;
  protocolo: string;
  status: ProtocoloStatus;
  data: string;
  error_message?: string | null;
}

export interface StagingEntry {
  id: number;
  conta_debito_raw: string;
  conta_credito_raw: string;
  data_lancamento: string;
  valor: number;
  historico: string;
  cod_historico: string;
}

export interface PendenciaGroup {
  protocolo_id: number;
  numero_protocolo: string;
  cnpj: string;
  entries: StagingEntry[];
}

export interface LoteContabilCreate {
  protocolo: string;
  cnpj: string;
  codigo_matriz: number;
  codigo_filial?: number;
  periodo: string;
  lote_inicial?: number;
  email_destinatario: string;
  layout_nome: string;
  arquivo_base64: string;
}

export interface ResolvePendenciaRequest {
  protocolo_id: number;
  conta_cliente: string;
  conta_contabilidade: string;
  tipo: "DEBITO" | "CREDITO";
  cnpj_empresa: string;
}

export interface ConsultaProtocoloResponse {
  sucesso: boolean;
  protocolo: string;
  status: ProtocoloStatus;
  resultado: string;
  error_message?: string | null;
}

export interface ListaProtocolosResponse {
  sucesso: boolean;
  protocolos: Protocolo[];
}

export interface PendenciasResponse {
  sucesso: boolean;
  pendencias: PendenciaGroup[];
}

export interface ResolverResponse {
  sucesso: boolean;
  mensagem: string;
  reprocessando: boolean;
  contas_pendentes?: string[];
}
